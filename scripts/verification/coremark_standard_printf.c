/* Target-specific formatting only. Benchmark algorithms/framework are copied
 * unchanged. Floating output uses libgcc soft-double arithmetic, never libm. */
#include "coremark.h"
#include <stdarg.h>
extern void uart_send_char(char c);
extern int coremark_validated;

static int text(const char *s)
{ int n = 0; while (*s) { uart_send_char(*s++); n++; } return n; }

static int begins(const char *s, const char *prefix)
{ while (*prefix) if (*s++ != *prefix++) return 0; return 1; }

static int number(ee_u32 value, unsigned base, unsigned width)
{
    char b[32]; unsigned n = 0, printed;
    do { b[n++] = "0123456789abcdef"[value % base]; value /= base; } while (value);
    printed = n > width ? n : width;
    while (width > n) { uart_send_char('0'); width--; }
    while (n) uart_send_char(b[--n]);
    return (int)printed;
}

int ee_printf(const char *fmt, ...)
{
    va_list ap; int n = 0;
    if (begins(fmt, "Correct operation validated.")) coremark_validated = 1;
    if (begins(fmt, "ERROR") || begins(fmt, "Errors detected") ||
        begins(fmt, "Cannot validate")) coremark_validated = 0;
    va_start(ap, fmt);
    while (*fmt) {
        unsigned width = 0; int wide = 0;
        if (*fmt != '%') { uart_send_char(*fmt++); n++; continue; }
        fmt++;
        if (*fmt == '0') fmt++;
        while (*fmt >= '0' && *fmt <= '9') width = width * 10 + (*fmt++ - '0');
        if (*fmt == 'l') { wide = 1; fmt++; }
        switch (*fmt++) {
        case 's': n += text(va_arg(ap, const char *)); break;
        case 'd': {
            ee_s32 v = wide ? (ee_s32)va_arg(ap, long) : va_arg(ap, int);
            if (v < 0) { uart_send_char('-'); n++; }
            n += number(v < 0 ? 0u - (ee_u32)v : (ee_u32)v, 10, width); break;
        }
        case 'u': case 'x': {
            char code = fmt[-1];
            ee_u32 v = wide ? (ee_u32)va_arg(ap, unsigned long) : va_arg(ap, unsigned int);
            n += number(v, code == 'x' ? 16 : 10, width); break;
        }
#if HAS_FLOAT
        case 'f': {
            double v = va_arg(ap, double); ee_u32 whole, frac;
            if (v < 0) { uart_send_char('-'); n++; v = -v; }
            whole = (ee_u32)v;
            frac = (ee_u32)((v - (double)whole) * 1000000.0 + 0.5);
            if (frac == 1000000u) { whole++; frac = 0; }
            n += number(whole, 10, 0); uart_send_char('.'); n++;
            n += number(frac, 10, 6); break;
        }
#endif
        case '%': uart_send_char('%'); n++; break;
        default: coremark_validated = 0; n += text("FORMAT_ERROR"); break;
        }
    }
    va_end(ap); return n;
}
