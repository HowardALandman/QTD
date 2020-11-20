#!/usr/bin/perl
# Do bootstrap Monte Carlo analysis on muon data.

# Read original count file.
@data = <>;

# Build an array of each data point.
# This is a little wasteful of space, but simple.
$bin = 0;
@decays = ();
while ($count = shift(@data))
{
	$count = 0 + $count;	# Convert to an integer
	#print "Bin $bin had $count events.\n";
	while ($count > 0)
	{
		push(@decays,$bin);
		$count --;
	}
	$bin ++;
}
warn "Processed $bin bins.\n";

$n_decays = scalar @decays;
warn "Found $n_decays decay events.\n";

$DATA = "data.txt";
$LOG = "raw2.txt";
open(LOG,">>$LOG");
for ($pass=1; $pass<= 300; $pass++)
{
	warn "Pass $pass\n";
	@new_count = ();

	# Open count file for writing.
	open(DATA,">$DATA");
	# Create a resampled data set
	# Generate $n_decays decays and increment bins.
	for ($n = $n_decays; $n > 0; $n--)
	{
		# Sample
		$randombin = $decays[rand $n_decays];
		$new_count[$randombin] ++;
	}
	# Write out new count file.
	for ($b = 0; $b < $bin; $b++)
	{
		$c = 0 + $new_count[$b];
		print DATA "$c\n";
	}
	close(DATA);

	$result = `octave ../gd4.m`;
	@result = split("\n",$result);
	$result = pop(@result);
	print LOG "$result\n";
	warn "$result\n";
}
close(LOG);
