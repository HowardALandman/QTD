## Plot our data from teachspin
par(bg="white")

setwd("~/bin/Teachspin/data")
## Read actual data.
ZZY <- t(read.delim("howard.count",header=FALSE))
## Read hypothesis data.
ZZy <- t(read.delim("ZZ.hyp",header=FALSE))
x <- 1:length(ZZY)
## time vector in nS
t <- 20*x

## Create PDF file of plot, with font matching TeX font.
pdf("ZZ.pdf",family="Times")
## Create plot and plot data in it.
plot(t,ZZY,main="Decay time data and best exponential+noise fit",
     xlab="Decay Time (nS)",
     ylab="Number of events per 20 nS bin",cex=0.4)
## Plot hypothesis curve on top of data.
lines(t,ZZy,col="red",lwd=1.5)
## Plot zero line for comparison with tail noise level.
zeros <- 0*x
lines(x,zeros,col="blue",lwd=1.5)
## Close the file.
dev.off()
