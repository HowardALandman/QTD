#!/usr/bin/perl

$fu[0] = 1;
$fu[999] = 1;
$length = @fu;
$length2 = scalar(@fu);
$length3 = $#fu;

print "length = $length, scalar length = $length2, end = $length3\n";
