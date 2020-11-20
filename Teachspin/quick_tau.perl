#!/usr/bin/perl
# Parse a data file from a Teachspin experiment
# and convert it into counts of the number of
# decay events at each bin time.
# Then use a simple stupid algorithm to find the lifetime tau.

# Split filename for later use.
#($root,$suffix) = split(/\./,$ARGV[0]);
#if ($suffix ne "data")
#{
#	print STDERR "WARNING: bad filename: $ARGV[0]\n";
#}

$events = 0;		# total events seen
$seconds = 0;		# total number of 1-second summaries
$min_decay = 99999;	# ~100 uS, longer than decay window
$max_decay = 0;
$decay_window = 20000;	# nS, = 20 uS
$bin_size = 20; 	# nS
$tau_nominal = 2200;	# nS
$start_time = -1;
$end_time = -1;

while (<>)
{
	if (/^4(\d\d\d\d) (\d+)/)
	{
		# 1-second summary record
		$n = $1;	# number of events
		$t = $2;	# timestamp
		# Keep track of earliest and latest timestamps
		# All timestamps appear to be generated in order,
		# but we code as if that might not be true.
		if (($start_time < 0) || ($t < $start_time))
		{
			$start_time = $t;
		}
		if ($t > $end_time)
		{
			$end_time = $t;
		}
		$events += $n;
		$seconds ++;
	}
	elsif (/(\d+) \d+/)
	{
		# Decay event record.
		# $1 is the decay time in nS.
		# It should always be a multiple of 20 nS.
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

# Check seconds count
$time = $end_time - $start_time + 1;
if ($seconds != $time)
{
	$diff = $time - $seconds;
	print "Timing mismatch: $seconds seconds vs ";
	print "$time computed time ($diff missing)\n" ;
}

# Calculate estimated noise distribution
# based on number of transit events.
$arrival_rate = $events / $seconds;
print "$events events in $seconds seconds\n";
print "Average arrival rate $arrival_rate events/second\n" ;
$decay_rate = $decays / $seconds;
print "$decays decays\n";
print "Average decay rate $decay_rate decays/second\n" ;

# Let's look at that issue:
print "Shortest decay was $min_decay nS\n";
# On most large datasets this gives 40 nS,
# so we ARE losing short decay events.
#print "Longest decay was $max_decay nS\n";
# It looks like the device is rounding to the nearest 20 nS
# and reports zero events for 0 nS and 20 nS bins.
# Also, the 40 nS bin usually has fewer events than the
# 60 nS bin, so we are probably losing some 40 nS events.

$n_bins = $decay_window / $bin_size;
print "$n_bins bins of $bin_size nS each ";
print "in a window of $decay_window nS\n";

# Fix the beginning problems by cutting off
# the initial empty bins and the first nonempty bin
# (which may only be partially full).
# For consistency delete first 3 bins from all datasets.
for ($i = 1; $i <= 3; $i++)
{
	$n = 0 + shift(@decay);
	print "Discarded initial bin with $n decays\n";
	$decays -= $n;
	$n_bins --;
}
print "$decays decays in $n_bins bins remaining\n";

# Construct output data file name.
#$COUNT_FILE = "$root.count";
# Write output data.
#open(COUNT_FILE,">$COUNT_FILE");
#for ($i = 0; $i < 997; $i++)
#{
#	print COUNT_FILE (0 + $decay[$i]), "\n";
#}
#close(COUNT_FILE);
#print "Wrote 997 lines to $COUNT_FILE\n";

# Initial guesses
$tau = 997 * $b / 2.0;	# a little less than 10 uS, 5X too big
			# but includes all original data
for ($i = 1; $i <= 100; $i++)
{
	$width = 2*$tau_prime;	# truncated window size for next
}
