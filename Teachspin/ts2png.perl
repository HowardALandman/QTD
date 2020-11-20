#!/usr/bin/perl

use GD;

$events = 0;
$seconds = 0;
$min_decay = 99999;	# approx 100 uS
$max_decay = 0;
$decay_window = 20000;	# 20 uS
$bin_size = 20; # nS
$tau_nominal = 2200;	# nS
$start_time = -1;
$end_time = -1;

while (<>)
{
	if (/^4(\d\d\d\d) (\d+)/)
	{
		$n = $1;
		$t = $2;
		if ($start_time < 0)
		{
			$start_time = $t;
		}
		$end_time = $t;
		$events += $n;
		$seconds ++;
		$offset = $t - $start_time;
		$value[$offset] = ($n >= 255) ? 255 : ($n + 1);
	}
	elsif (/(\d+) \d+/)
	{
		$bin = int(0.5 + $1 / $bin_size);
		if ($1 != $bin * $bin_size)
		{
			print "Rounding error on $1\n";
		}
		$decay[$bin] ++;
		$decays ++;
		if ($1 < $min_decay)
		{
			$min_decay = $1;
		}
		if ($1 > $max_decay)
		{
			$max_decay = $1;
		}
	}
	else
	{
		print "Couldn't parse: $_";
	}
}

$n_pixels = $end_time - $start_time + 1;

# Convert the data to an image

$im = new GD::Image

# Allocate color map
$c[0] = $im->colorAllocate(0,0,0);	# black for no data
$c[1] = $im->colorAllocate(0,0,255);	# blue for data = 0
$c[2] = $im->colorAllocate(0,255,0);	# nonzero data gets green to red
$c[3] = $im->colorAllocate(2,255,0);
$c[4] = $im->colorAllocate(4,255,0);
$c[5] = $im->colorAllocate(6,255,0);
$c[6] = $im->colorAllocate(8,255,0);
$c[7] = $im->colorAllocate(10,255,0);
$c[8] = $im->colorAllocate(12,255,0);
$c[9] = $im->colorAllocate(14,255,0);
$c[10] = $im->colorAllocate(16,255,0);
$c[11] = $im->colorAllocate(18,255,0);
$c[12] = $im->colorAllocate(20,255,0);
$c[13] = $im->colorAllocate(22,255,0);
$c[14] = $im->colorAllocate(24,255,0);
$c[15] = $im->colorAllocate(26,255,0);
$c[16] = $im->colorAllocate(28,255,0);
$c[17] = $im->colorAllocate(30,255,0);
$c[18] = $im->colorAllocate(32,255,0);
$c[19] = $im->colorAllocate(34,255,0);
$c[20] = $im->colorAllocate(36,255,0);
$c[21] = $im->colorAllocate(38,255,0);
$c[22] = $im->colorAllocate(40,255,0);
$c[23] = $im->colorAllocate(42,255,0);
$c[24] = $im->colorAllocate(44,255,0);
$c[25] = $im->colorAllocate(46,255,0);
$c[26] = $im->colorAllocate(48,255,0);
$c[27] = $im->colorAllocate(50,255,0);
$c[28] = $im->colorAllocate(52,255,0);
$c[29] = $im->colorAllocate(54,255,0);
$c[30] = $im->colorAllocate(56,255,0);
$c[31] = $im->colorAllocate(58,255,0);
$c[32] = $im->colorAllocate(60,255,0);
$c[33] = $im->colorAllocate(62,255,0);
$c[34] = $im->colorAllocate(64,255,0);
$c[35] = $im->colorAllocate(66,255,0);
$c[36] = $im->colorAllocate(68,255,0);
$c[37] = $im->colorAllocate(70,255,0);
$c[38] = $im->colorAllocate(72,255,0);
$c[39] = $im->colorAllocate(74,255,0);
$c[40] = $im->colorAllocate(76,255,0);
$c[41] = $im->colorAllocate(78,255,0);
$c[42] = $im->colorAllocate(80,255,0);
$c[43] = $im->colorAllocate(82,255,0);
$c[44] = $im->colorAllocate(84,255,0);
$c[45] = $im->colorAllocate(86,255,0);
$c[46] = $im->colorAllocate(88,255,0);
$c[47] = $im->colorAllocate(90,255,0);
$c[48] = $im->colorAllocate(92,255,0);
$c[49] = $im->colorAllocate(94,255,0);
$c[50] = $im->colorAllocate(96,255,0);
$c[51] = $im->colorAllocate(98,255,0);
$c[52] = $im->colorAllocate(100,255,0);
$c[53] = $im->colorAllocate(102,255,0);
$c[54] = $im->colorAllocate(104,255,0);
$c[55] = $im->colorAllocate(106,255,0);
$c[56] = $im->colorAllocate(108,255,0);
$c[57] = $im->colorAllocate(110,255,0);
$c[58] = $im->colorAllocate(112,255,0);
$c[59] = $im->colorAllocate(114,255,0);
$c[60] = $im->colorAllocate(116,255,0);
$c[61] = $im->colorAllocate(118,255,0);
$c[62] = $im->colorAllocate(120,255,0);
$c[63] = $im->colorAllocate(122,255,0);
$c[64] = $im->colorAllocate(124,255,0);
$c[65] = $im->colorAllocate(126,255,0);
$c[66] = $im->colorAllocate(128,255,0);
$c[67] = $im->colorAllocate(130,255,0);
$c[68] = $im->colorAllocate(132,255,0);
$c[69] = $im->colorAllocate(134,255,0);
$c[70] = $im->colorAllocate(136,255,0);
$c[71] = $im->colorAllocate(138,255,0);
$c[72] = $im->colorAllocate(140,255,0);
$c[73] = $im->colorAllocate(142,255,0);
$c[74] = $im->colorAllocate(144,255,0);
$c[75] = $im->colorAllocate(146,255,0);
$c[76] = $im->colorAllocate(148,255,0);
$c[77] = $im->colorAllocate(150,255,0);
$c[78] = $im->colorAllocate(152,255,0);
$c[79] = $im->colorAllocate(154,255,0);
$c[80] = $im->colorAllocate(156,255,0);
$c[81] = $im->colorAllocate(158,255,0);
$c[82] = $im->colorAllocate(160,255,0);
$c[83] = $im->colorAllocate(162,255,0);
$c[84] = $im->colorAllocate(164,255,0);
$c[85] = $im->colorAllocate(166,255,0);
$c[86] = $im->colorAllocate(168,255,0);
$c[87] = $im->colorAllocate(170,255,0);
$c[88] = $im->colorAllocate(172,255,0);
$c[89] = $im->colorAllocate(174,255,0);
$c[90] = $im->colorAllocate(176,255,0);
$c[91] = $im->colorAllocate(178,255,0);
$c[92] = $im->colorAllocate(180,255,0);
$c[93] = $im->colorAllocate(182,255,0);
$c[94] = $im->colorAllocate(184,255,0);
$c[95] = $im->colorAllocate(186,255,0);
$c[96] = $im->colorAllocate(188,255,0);
$c[97] = $im->colorAllocate(190,255,0);
$c[98] = $im->colorAllocate(192,255,0);
$c[99] = $im->colorAllocate(194,255,0);
$c[100] = $im->colorAllocate(196,255,0);
$c[101] = $im->colorAllocate(198,255,0);
$c[102] = $im->colorAllocate(200,255,0);
$c[103] = $im->colorAllocate(202,255,0);
$c[104] = $im->colorAllocate(204,255,0);
$c[105] = $im->colorAllocate(206,255,0);
$c[106] = $im->colorAllocate(208,255,0);
$c[107] = $im->colorAllocate(210,255,0);
$c[108] = $im->colorAllocate(212,255,0);
$c[109] = $im->colorAllocate(214,255,0);
$c[110] = $im->colorAllocate(216,255,0);
$c[111] = $im->colorAllocate(218,255,0);
$c[112] = $im->colorAllocate(220,255,0);
$c[113] = $im->colorAllocate(222,255,0);
$c[114] = $im->colorAllocate(224,255,0);
$c[115] = $im->colorAllocate(226,255,0);
$c[116] = $im->colorAllocate(228,255,0);
$c[117] = $im->colorAllocate(230,255,0);
$c[118] = $im->colorAllocate(232,255,0);
$c[119] = $im->colorAllocate(234,255,0);
$c[120] = $im->colorAllocate(236,255,0);
$c[121] = $im->colorAllocate(238,255,0);
$c[122] = $im->colorAllocate(240,255,0);
$c[123] = $im->colorAllocate(242,255,0);
$c[124] = $im->colorAllocate(244,255,0);
$c[125] = $im->colorAllocate(246,255,0);
$c[126] = $im->colorAllocate(248,255,0);
$c[127] = $im->colorAllocate(250,255,0);
$c[128] = $im->colorAllocate(252,255,0);
$c[129] = $im->colorAllocate(254,255,0);	# yellow here
$c[130] = $im->colorAllocate(255,254,0);	# head to red
$c[131] = $im->colorAllocate(255,252,0);
$c[132] = $im->colorAllocate(255,250,0);
$c[133] = $im->colorAllocate(255,248,0);
$c[134] = $im->colorAllocate(255,246,0);
$c[135] = $im->colorAllocate(255,244,0);
$c[136] = $im->colorAllocate(255,242,0);
$c[137] = $im->colorAllocate(255,240,0);
$c[138] = $im->colorAllocate(255,238,0);
$c[139] = $im->colorAllocate(255,236,0);
$c[140] = $im->colorAllocate(255,234,0);
$c[141] = $im->colorAllocate(255,232,0);
$c[142] = $im->colorAllocate(255,230,0);
$c[143] = $im->colorAllocate(255,228,0);
$c[144] = $im->colorAllocate(255,226,0);
$c[145] = $im->colorAllocate(255,224,0);
$c[146] = $im->colorAllocate(255,222,0);
$c[147] = $im->colorAllocate(255,220,0);
$c[148] = $im->colorAllocate(255,218,0);
$c[149] = $im->colorAllocate(255,216,0);
$c[150] = $im->colorAllocate(255,214,0);
$c[151] = $im->colorAllocate(255,212,0);
$c[152] = $im->colorAllocate(255,210,0);
$c[153] = $im->colorAllocate(255,208,0);
$c[154] = $im->colorAllocate(255,206,0);
$c[155] = $im->colorAllocate(255,204,0);
$c[156] = $im->colorAllocate(255,202,0);
$c[157] = $im->colorAllocate(255,200,0);
$c[158] = $im->colorAllocate(255,198,0);
$c[159] = $im->colorAllocate(255,196,0);
$c[160] = $im->colorAllocate(255,194,0);
$c[161] = $im->colorAllocate(255,192,0);
$c[162] = $im->colorAllocate(255,190,0);
$c[163] = $im->colorAllocate(255,188,0);
$c[164] = $im->colorAllocate(255,186,0);
$c[165] = $im->colorAllocate(255,184,0);
$c[166] = $im->colorAllocate(255,182,0);
$c[167] = $im->colorAllocate(255,180,0);
$c[168] = $im->colorAllocate(255,178,0);
$c[169] = $im->colorAllocate(255,176,0);
$c[170] = $im->colorAllocate(255,174,0);
$c[171] = $im->colorAllocate(255,172,0);
$c[172] = $im->colorAllocate(255,170,0);
$c[173] = $im->colorAllocate(255,168,0);
$c[174] = $im->colorAllocate(255,166,0);
$c[175] = $im->colorAllocate(255,164,0);
$c[176] = $im->colorAllocate(255,162,0);
$c[177] = $im->colorAllocate(255,160,0);
$c[178] = $im->colorAllocate(255,158,0);
$c[179] = $im->colorAllocate(255,156,0);
$c[180] = $im->colorAllocate(255,154,0);
$c[181] = $im->colorAllocate(255,152,0);
$c[182] = $im->colorAllocate(255,150,0);
$c[183] = $im->colorAllocate(255,148,0);
$c[184] = $im->colorAllocate(255,146,0);
$c[185] = $im->colorAllocate(255,144,0);
$c[186] = $im->colorAllocate(255,142,0);
$c[187] = $im->colorAllocate(255,140,0);
$c[188] = $im->colorAllocate(255,138,0);
$c[189] = $im->colorAllocate(255,136,0);
$c[190] = $im->colorAllocate(255,134,0);
$c[191] = $im->colorAllocate(255,132,0);
$c[192] = $im->colorAllocate(255,130,0);
$c[193] = $im->colorAllocate(255,128,0);
$c[194] = $im->colorAllocate(255,126,0);
$c[195] = $im->colorAllocate(255,124,0);
$c[196] = $im->colorAllocate(255,122,0);
$c[197] = $im->colorAllocate(255,120,0);
$c[198] = $im->colorAllocate(255,118,0);
$c[199] = $im->colorAllocate(255,116,0);
$c[200] = $im->colorAllocate(255,114,0);
$c[201] = $im->colorAllocate(255,112,0);
$c[202] = $im->colorAllocate(255,110,0);
$c[203] = $im->colorAllocate(255,108,0);
$c[204] = $im->colorAllocate(255,106,0);
$c[205] = $im->colorAllocate(255,104,0);
$c[206] = $im->colorAllocate(255,102,0);
$c[207] = $im->colorAllocate(255,100,0);
$c[208] = $im->colorAllocate(255,98,0);
$c[209] = $im->colorAllocate(255,96,0);
$c[210] = $im->colorAllocate(255,94,0);
$c[211] = $im->colorAllocate(255,92,0);
$c[212] = $im->colorAllocate(255,90,0);
$c[213] = $im->colorAllocate(255,88,0);
$c[214] = $im->colorAllocate(255,86,0);
$c[215] = $im->colorAllocate(255,84,0);
$c[216] = $im->colorAllocate(255,82,0);
$c[217] = $im->colorAllocate(255,80,0);
$c[218] = $im->colorAllocate(255,78,0);
$c[219] = $im->colorAllocate(255,76,0);
$c[220] = $im->colorAllocate(255,74,0);
$c[221] = $im->colorAllocate(255,72,0);
$c[222] = $im->colorAllocate(255,70,0);
$c[223] = $im->colorAllocate(255,68,0);
$c[224] = $im->colorAllocate(255,66,0);
$c[225] = $im->colorAllocate(255,64,0);
$c[226] = $im->colorAllocate(255,62,0);
$c[227] = $im->colorAllocate(255,60,0);
$c[228] = $im->colorAllocate(255,58,0);
$c[229] = $im->colorAllocate(255,56,0);
$c[230] = $im->colorAllocate(255,54,0);
$c[231] = $im->colorAllocate(255,52,0);
$c[232] = $im->colorAllocate(255,50,0);
$c[233] = $im->colorAllocate(255,48,0);
$c[234] = $im->colorAllocate(255,46,0);
$c[235] = $im->colorAllocate(255,44,0);
$c[236] = $im->colorAllocate(255,42,0);
$c[237] = $im->colorAllocate(255,40,0);
$c[238] = $im->colorAllocate(255,38,0);
$c[239] = $im->colorAllocate(255,36,0);
$c[240] = $im->colorAllocate(255,34,0);
$c[241] = $im->colorAllocate(255,32,0);
$c[242] = $im->colorAllocate(255,30,0);
$c[243] = $im->colorAllocate(255,28,0);
$c[244] = $im->colorAllocate(255,26,0);
$c[245] = $im->colorAllocate(255,24,0);
$c[246] = $im->colorAllocate(255,22,0);
$c[247] = $im->colorAllocate(255,20,0);
$c[248] = $im->colorAllocate(255,18,0);
$c[249] = $im->colorAllocate(255,16,0);
$c[250] = $im->colorAllocate(255,14,0);
$c[251] = $im->colorAllocate(255,12,0);
$c[252] = $im->colorAllocate(255,10,0);
$c[253] = $im->colorAllocate(255,8,0);
$c[254] = $im->colorAllocate(255,6,0);
$c[255] = $im->colorAllocate(255,0,0);

# Check that we got them all
for ($i = 0; $i < 256; $i++)
{
	if ($c[$i] != $i)
	{
		die "FATAL: colormap: c[$i] = $c[$i]\n";
	}
}
