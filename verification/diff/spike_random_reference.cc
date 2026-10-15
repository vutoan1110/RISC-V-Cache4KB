// Spike ISA engine adapter for the frozen split-memory random core tests.
// The programs access only data0x400..0x4ff, disjoint from instruction bytes.
// No ISA semantics, result values or RTL trace data are implemented here.
#include <riscv/processor.h>
#include <riscv/simif.h>
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>

class Memory : public simif_t {
 public:
  cfg_t cfg;
  std::array<char,4096> bytes{};
  std::map<size_t,processor_t*> harts;
  char* addr_to_mem(reg_t address) override {
    return address < bytes.size() ? bytes.data()+address : nullptr;
  }
  bool mmio_load(reg_t,size_t,uint8_t*) override { return false; }
  bool mmio_store(reg_t,size_t,const uint8_t*) override { return false; }
  void proc_reset(unsigned) override {}
  const cfg_t& get_cfg() const override { return cfg; }
  const std::map<size_t,processor_t*>& get_harts() const override { return harts; }
  const char* get_symbol(uint64_t) override { return nullptr; }
};

int main(int argc,char** argv) {
  try {
    if(argc!=2) throw std::runtime_error("require one generated hex input");
    Memory memory;
    memory.cfg.isa="RV32I_Zmmul";
    memory.cfg.priv="M";
    std::ifstream input(argv[1]);
    if(!input) throw std::runtime_error("cannot read hex");
    uint32_t word=0; size_t count=0;
    while(input >> std::hex >> word) {
      if(count>=161) throw std::runtime_error("too many instruction words");
      for(unsigned b=0;b<4;b++) memory.bytes[count*4+b]=char(word>>(8*b));
      count++;
    }
    if(count!=161 || word!=0x6f) throw std::runtime_error("bad generated program");
    processor_t cpu(memory.cfg.isa,memory.cfg.priv,&memory.cfg,&memory,0,false,stdout,std::cerr);
    memory.harts[0]=&cpu;
    cpu.get_state()->pc=0;
    for(unsigned r=0;r<32;r++) cpu.get_state()->XPR.write(r,0);
    cpu.enable_log_commits();
    for(unsigned step=0;step<1000;step++) {
      reg_t pc=cpu.get_state()->pc;
      if(pc>640 || pc%4) throw std::runtime_error("trap/PC outside generated program");
      uint32_t instruction=0;
      for(unsigned b=0;b<4;b++) instruction|=uint32_t(uint8_t(memory.bytes[pc+b]))<<(8*b);
      cpu.step(1);
      if(instruction==0x6f) {
        if(pc!=640 || cpu.get_state()->pc!=640) throw std::runtime_error("bad HALT");
        std::cerr << "[PASS] Spike generated program reached HALT\n";
        return 0;
      }
    }
    throw std::runtime_error("instruction bound exhausted");
  } catch(const std::exception& error) {
    std::cerr << "[FAIL] " << error.what() << '\n';
    return 1;
  }
}
