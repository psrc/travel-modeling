# This script will create 2 csv files:
# 1) buildings (housing units)
# 2) parcels with GQ land use

library(RMySQL)
library(data.table)

data.outdir <- "W:/gis/projects/parcelization"
dbname <- 'psrc_2014_parcel_baseyear'

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
  mydb <- mysql.conn(dbname)
  rs <- dbSendQuery(mydb, paste0("select * from ", table))
  data <- fetch(rs, n = -1)
  setDT(data)
  dbClearResult(rs)
  dbDisconnect(mydb)
  return(data)
}

# Generate buildings file
bldgs <- get.table(dbname, "buildings")
write.csv(bldgs, file.path(data.outdir, "gq_2014.csv", row.names = F))

# Generate GQ file
prcl <- get.table(dbname, "parcels")
lut <- get.table(dbname, "land_use_types")
pl <- merge(prcl, lutype, by = 'land_use_type_id')
gqs <- pl[description == 'Group Quarters',]
write.csv(gqs, file.path(data.outdir, "gq_2014.csv", row.names = F))
          

