# This script will create 2 csv files:
# 1) buildings (housing units)
# 2) parcels with GQ land use

library(RMySQL)
library(data.table)

data.outdir <- "W:/gis/projects/parcelization"
dbname <- '2018_parcel_baseyear' #'psrc_2014_parcel_baseyear'

mysql.conn <- function(dbname) {
  un <- .rs.askForPassword("username:")
  psswd <- .rs.askForPassword("password:")
  h <- .rs.askForPassword("host:")
  mydb <- dbConnect(MySQL(),
                    user = un,
                    password = psswd,
                    dbname = dbname,
                    host = h)
}

get.table <- function(dbname, table) {
  rs <- dbSendQuery(mydb, paste0("select * from ", table))
  data <- fetch(rs, n = -1)
  setDT(data)
  dbClearResult(rs)
  return(data)
}

mydb <- mysql.conn(dbname)

# Generate buildings file
bldgs <- get.table(dbname, "buildings")
fwrite(bldgs, file.path(data.outdir, "buildings_2018.csv"), row.names = FALSE)

# Generate GQ file
prcl <- get.table(dbname, "parcels")
lut <- get.table(dbname, "land_use_types")
pl <- merge(prcl, lut, by = 'land_use_type_id')
gqs <- pl[description == 'Group Quarters',]
fwrite(gqs, file.path(data.outdir, "gq_2018.csv"), row.names = FALSE)
          
dbDisconnect(mydb)
