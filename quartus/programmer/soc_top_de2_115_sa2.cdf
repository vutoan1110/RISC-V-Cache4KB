/* Quartus Programmer chain for the default DE2-115 SA2 build. */
JedecChain;
	FileRevision(JESD32A);
	DefaultMfr(6E);

	P ActionCode(Cfg)
		Device PartName(EP4CE115F29) Path("../../output_files_de2_115_sa2/") File("soc_top_de2_115_sa2.sof") MfrSpec(OpMask(1));

ChainEnd;

Altera Begin;
	ChainType(JTAG);
Altera End;
