#!/usr/bin/perl
# Take the hypothesis parameters from a gradient descent fit
# of Teachspin data, and write out a detailed error analysis
# in TeX format for the paper.

sub do_line {
my($a,$n,$tau,$nu) = @_;
print "dataset=$a, n=$n, tau=$tau, nu=$nu (nu is currently ignored)\n";

$b = 20; 	# bin size in nS

$i = 0;

# delta_trig
#$name[$i] = '$\delta_{trig}$';
$name[$i] = '$\sigma_{trig}$';
#$offset[$i] = -14.5;
$offset[$i] = 0.0;
#$trig_offset = -14.5;
$trig_offset = 0.0;
$sigma[$i] = 1.45 + 9.5/sqrt($n);
$i++;

# sigma_p
#$name[$i] = '$\sigma_{p}$';
#$offset[$i] = 0.0;
#$sigma[$i] = 4.0;
#$i++;

# sigma_ms
#$name[$i] = '$\sigma_{ms}$';
#$offset[$i] = 0.0;
#$sigma[$i] = 0.1;
#$i++;

# delta_dig
$name[$i] = '$\delta_{dig}$';
#$offset[$i] = $tau - $b/(exp($b/$tau) - 1);
$offset[$i] = 0.0;
$sigma[$i] = 0.5*$b/sqrt(3*$n);
$i++;

# delta_clock
$name[$i] = '$\delta_{ck}$';
$offset[$i] = 0.0;
$sigma[$i] = 0.0001*$tau;
$i++;

# sigma_binom
$name[$i] = '$\sigma_{binom}$';
$offset[$i] = 0.0;
$sigma[$i] = 76.94/sqrt($n);
$i++;

# print them all out
$i_max = $i;

# header line, first time only
if (!$header_printed)
{
	print $a;
	print ' & $\tau_{adj}$ ';
	for ($i=0; $i<$i_max; $i++)
	{
		print "& $name[$i] ";
	}
	print "\n";
	$header_printed = 1;
}

# data line
print ' & ', $tau + $trig_offset, ' & $';
for ($i=0; $i<$i_max; $i++)
{
	if ($offset[$i] != 0.0)
	{
		print $offset[$i];
	}
	if ($sigma[$i] != 0.0)
	{
		print "\\pm$sigma[$i]";
	}
	print '$ ';
}
print "\n";

# Additionally, write out a detailed bin-by-bin model of the
# hypothesis in the same format as the summary data files.
	$one_minus_p = exp(-$b/$tau);
	$p = 1 - $one_minus_p;
	$decay = $p * $n;	# number expected to decay in first bin
	$AFILE = "$a.hyp";
	open(AFILE,">$AFILE");
	for ($i=0; $i<997; $i++)
	{
		$hyp = $decay + $nu;
		print AFILE "$hyp\n";
		$decay *= $one_minus_p;
	}
	close AFILE;
}

# Process all data sets.
&do_line('D',   8340.885384, 1991.954669, 0.602296);
&do_line('E',   3905.128384, 1753.169409, -0.760365);
&do_line('H',  20161.148389, 1985.457413, 1.446067);
&do_line('M',  12984.064489, 1903.078861, 0.819760);
&do_line('P',  25717.742580, 1941.212151, -5.703965);
&do_line('S',   2330.060498, 1981.906108, 0.232737);
&do_line('Y',   6502.150953, 2021.043352, 0.562875);
&do_line('Z1',  6332.506662, 2040.646386, 0.348901);
&do_line('Z2',  9664.946710, 1977.263647, 0.733657);
&do_line('Z3', 20049.800011, 2056.299940, 1.319391);
&do_line('ZZ', 36044.133506, 2031.792283, 2.405053);

