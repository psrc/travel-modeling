library(plotKML)

# GPX files downloaded from Runkeeper
folder <- "data\\"
files <- dir(folder, recursive=TRUE, pattern = "\\.csv")

# Consolidate routes in one drata frame
index <- c()
latitude <- c()
longitude <- c()
trip <- c()

for (i in 1:length(files)) {
	

  route <- read.csv(paste(folder,files[i], sep =""), header = FALSE)
	#location <- route$tracks[[1]][[1]]
	
	index <- c(index, rep(i, dim(route)[1]))
	latitude <- c(latitude, route[,2])
	longitude <- c(longitude, route[,3])
  trip <- c(trip, route)
}
routes <- data.frame(cbind(index, latitude, longitude))

# Map the routes
ids <- unique(index)
plot(routes$longitude, routes$latitude, type="n", axes=FALSE, xlab="", ylab="", main="", asp=1, xlim=c(-122.4, -122.3), ylim=c(47.6, 47.7))
for (i in 1:length(ids)) {
	currRoute <- subset(routes, index==ids[i])
	lines(currRoute$longitude, currRoute$latitude, col="#00000020")
}