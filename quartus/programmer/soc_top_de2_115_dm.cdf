/* Quartus Programmer chain for the DE2-115 direct-mapped build. */
JedecChain;
	FileRevision(JESD32A);
	DefaultMfr(6E);

	P ActionCode(Cfg)
		Device PartName(EP4CE115F29) Path("../../output_files_de2_115_dm/") File("soc_top_de2_115_dm.sof") MfrSpec(OpMask(1));

ChainEnd;

Altera Begin;
	ChainType(JTAG);
Altera End;
