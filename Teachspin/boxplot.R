## Plot our data from teachspin
par(bg="white")

setwd("~/bin/Teachspin/data")
ZZy <- t(read.delim("ZZ.hyp",header=FALSE))
ZZY <- t(read.delim("howard.count",header=FALSE))
x <- 1:length(ZZY)
## plot data
plot(x,ZZY)
## plot model
lines(x,ZZy)
## plot zero line
zeros <- x
zeros[1:length(x)] <- 0
lines(x,zeros,col="blue")
##boxplot(x, col="lavender")
##title(main="Boxplot", xlab="Bin")
