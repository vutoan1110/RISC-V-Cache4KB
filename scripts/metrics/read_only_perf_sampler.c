/* Bounded user-mode instruction sampling; no ptrace, signals or target memory reads. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <linux/perf_event.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

enum { TARGET = 669, DATA_PAGES = 8, MAX_SAMPLES = 2048 };
static const char *expected_exe = "/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/.openroad-wrapped";
static const char *expected_run = "vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1/43-openroad-detailedrouting";
static char target_exe[4096], cmdline[16384], start_stat[8192], end_stat[8192];
struct sample { uint64_t ip, time; uint32_t pid, tid; uint16_t misc; };
static struct sample samples[MAX_SAMPLES];
static size_t sample_count;
static uint64_t lost, records, non_sample_records;
static double elapsed;
static int event_enabled;

static void quoted(const char *s) {
    putchar('"');
    for (; *s; ++s) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') { putchar('\\'); putchar(c); }
        else if (c < 32) printf("\\u%04x", c);
        else putchar(c);
    }
    putchar('"');
}

static void receipt(const char *status, const char *stage, int error) {
    printf("{\"status\":"); quoted(status);
    printf(",\"stage\":"); quoted(stage);
    printf(",\"errno\":%d,\"error\":", error); quoted(error ? strerror(error) : "");
    printf(",\"target_tid\":%d,\"period_ns\":50000000,\"max_wall_seconds\":5,", TARGET);
    printf("\"exclude_kernel\":true,\"exclude_hv\":true,\"inherit\":false,\"event_was_enabled\":%s,", event_enabled ? "true" : "false");
    printf("\"elapsed_seconds\":%.9f,\"records\":%" PRIu64 ",\"lost\":%" PRIu64 ",\"other_records\":%" PRIu64 ",", elapsed, records, lost, non_sample_records);
    printf("\"actual_executable\":"); quoted(target_exe);
    printf(",\"actual_cmdline\":"); quoted(cmdline);
    printf(",\"start_proc_stat\":"); quoted(start_stat);
    printf(",\"end_proc_stat\":"); quoted(end_stat);
    printf(",\"samples\":[");
    for (size_t i = 0; i < sample_count; ++i) {
        if (i) putchar(',');
        printf("{\"ip\":\"0x%" PRIx64 "\",\"pid\":%u,\"tid\":%u,\"time_ns\":%" PRIu64 ",\"misc\":%u}",
               samples[i].ip, samples[i].pid, samples[i].tid, samples[i].time, samples[i].misc);
    }
    puts("]}");
}

static ssize_t read_file(const char *path, char *buffer, size_t capacity) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    ssize_t size = read(fd, buffer, capacity - 1);
    int saved = errno;
    close(fd);
    errno = saved;
    if (size >= 0) buffer[size] = 0;
    return size;
}

static double seconds(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static int same_start_time(const char *before, const char *after) {
    const char *a = strrchr(before, ')'), *b = strrchr(after, ')');
    if (!a || !b) return 0;
    ++a; ++b;
    /* After comm, field3 is first token; compare field22 (starttime). */
    for (int field = 3; field <= 22; ++field) {
        while (*a == ' ') ++a;
        while (*b == ' ') ++b;
        const char *ae = a, *be = b;
        while (*ae && *ae != ' ') ++ae;
        while (*be && *be != ' ') ++be;
        if (field == 22) return ae > a && (ae-a) == (be-b) && !memcmp(a,b,(size_t)(ae-a));
        a = ae; b = be;
    }
    return 0;
}

static void ring_copy(const unsigned char *data, uint64_t size, uint64_t offset, void *out, size_t bytes) {
    uint64_t index = offset % size;
    size_t first = bytes;
    if (first > size - index) first = (size_t)(size - index);
    memcpy(out, data + index, first);
    if (first < bytes) memcpy((unsigned char*)out + first, data, bytes - first);
}

static int drain(struct perf_event_mmap_page *meta, unsigned char *data, uint64_t size, uint64_t *tail) {
    uint64_t head = __atomic_load_n(&meta->data_head, __ATOMIC_ACQUIRE);
    if (head < *tail || head - *tail > size) return EOVERFLOW;
    while (*tail < head) {
        struct perf_event_header h;
        if (head - *tail < sizeof(h)) return EPROTO;
        ring_copy(data, size, *tail, &h, sizeof(h));
        if (h.size < sizeof(h) || h.size > size || h.size > head - *tail) return EPROTO;
        ++records;
        if (h.type == PERF_RECORD_SAMPLE) {
            struct { uint64_t ip; uint32_t pid, tid; uint64_t time; } body;
            if (h.size != sizeof(h) + sizeof(body) || sample_count >= MAX_SAMPLES) return EOVERFLOW;
            ring_copy(data, size, *tail + sizeof(h), &body, sizeof(body));
            if (body.tid != TARGET || body.pid != TARGET || (h.misc & PERF_RECORD_MISC_CPUMODE_MASK) != PERF_RECORD_MISC_USER) return EPROTO;
            samples[sample_count++] = (struct sample){body.ip, body.time, body.pid, body.tid, h.misc};
        } else if (h.type == PERF_RECORD_LOST) {
            uint64_t body[2];
            if (h.size < sizeof(h) + sizeof(body)) return EPROTO;
            ring_copy(data, size, *tail + sizeof(h), body, sizeof(body));
            lost += body[1];
        } else ++non_sample_records;
        *tail += h.size;
    }
    __atomic_store_n(&meta->data_tail, *tail, __ATOMIC_RELEASE);
    return 0;
}

int main(int argc, char **argv) {
    (void)argv;
    if (argc != 1) { receipt("REJECTED", "unexpected_arguments", EINVAL); return 2; }
    struct stat identity;
    if (stat("/proc/669", &identity) || identity.st_uid != geteuid()) {
        receipt("REJECTED", "same_unprivileged_owner", errno ? errno : EPERM); return 2;
    }
    ssize_t count = readlink("/proc/669/exe", target_exe, sizeof(target_exe)-1);
    if (count < 0) { receipt("REJECTED", "executable_identity", errno); return 2; }
    target_exe[count] = 0;
    ssize_t bytes = read_file("/proc/669/cmdline", cmdline, sizeof(cmdline));
    if (bytes < 0) { receipt("REJECTED", "cmdline_identity", errno); return 2; }
    for (ssize_t i = 0; i < bytes; ++i) if (!cmdline[i]) cmdline[i] = ' ';
    if (strcmp(target_exe, expected_exe) || !strstr(cmdline, expected_run)) {
        receipt("REJECTED", "exact_run_identity", EINVAL); return 2;
    }
    if (read_file("/proc/669/stat", start_stat, sizeof(start_stat)) < 0) {
        receipt("REJECTED", "initial_proc_stat", errno); return 2;
    }
    struct perf_event_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.type = PERF_TYPE_SOFTWARE;
    attr.size = sizeof(attr);
    attr.config = PERF_COUNT_SW_CPU_CLOCK;
    attr.sample_period = 50000000;
    attr.sample_type = PERF_SAMPLE_IP | PERF_SAMPLE_TID | PERF_SAMPLE_TIME;
    attr.disabled = 1; attr.exclude_kernel = 1; attr.exclude_hv = 1;
    attr.wakeup_events = 1;
    int fd = (int)syscall(__NR_perf_event_open, &attr, TARGET, -1, -1, PERF_FLAG_FD_CLOEXEC);
    if (fd < 0) { receipt("PERF_EVENT_OPEN_FAILED_NO_RETRY", "perf_event_open", errno); return 3; }
    long page = sysconf(_SC_PAGESIZE);
    if (page < 4096 || page > 65536) { close(fd); receipt("REJECTED", "page_size", EINVAL); return 2; }
    size_t mapped_bytes = (size_t)page * (1 + DATA_PAGES);
    void *mapped = mmap(NULL, mapped_bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) { int error = errno; close(fd); receipt("SAMPLING_FAILED", "mmap", error); return 3; }
    struct perf_event_mmap_page *meta = mapped;
    if (meta->data_offset != (uint64_t)page || meta->data_size != (uint64_t)page * DATA_PAGES) {
        munmap(mapped, mapped_bytes); close(fd); receipt("REJECTED", "ring_layout", EPROTO); return 2;
    }
    uint64_t tail = meta->data_tail;
    unsigned char *data = (unsigned char*)mapped + meta->data_offset;
    int error = 0;
    if (ioctl(fd, PERF_EVENT_IOC_RESET, 0) || ioctl(fd, PERF_EVENT_IOC_ENABLE, 0)) error = errno;
    double begin = seconds();
    if (!error && begin >= 0) {
        event_enabled = 1;
        for (;;) {
            double current = seconds();
            if (current < 0) { error = errno; break; }
            elapsed = current - begin;
            error = drain(meta, data, meta->data_size, &tail);
            /* Reserve100ms for userspace scheduling and disable/cleanup. */
            if (error || elapsed >= 4.90) break;
            double remain = 4.90 - elapsed;
            double sleep_seconds = remain < .05 ? remain : .05;
            struct timespec pause = {0, (long)(sleep_seconds * 1e9)};
            if (nanosleep(&pause, NULL) && errno != EINTR) { error = errno; break; }
        }
    } else if (!error) error = errno;
    if (ioctl(fd, PERF_EVENT_IOC_DISABLE, 0) && !error) error = errno;
    if (event_enabled && elapsed > 5.0 && !error) error = ETIMEDOUT;
    if (!error) error = drain(meta, data, meta->data_size, &tail);
    munmap(mapped, mapped_bytes); close(fd);
    if (read_file("/proc/669/stat", end_stat, sizeof(end_stat)) < 0 && !error) error = errno;
    if (!same_start_time(start_stat, end_stat) && !error) error = ESRCH;
    receipt(error ? "SAMPLING_FAILED" : "COMPLETED_BOUNDED_USER_PC_SAMPLING", error ? "sampling_or_identity" : "complete", error);
    return error ? 3 : 0;
}
