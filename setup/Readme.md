# What is here

## Files distrib_setup*.json
    These files are configuration files that are can be used to define the:
        - day of the week that a restaurant works
        - day of the week that any competing activity is possible (mostly working hours of competitors)
        - the overall profile distribution of the afluence for a typical restaurant within the area (not only the restaurant subject to the study)
        - parameters for the yearly modulation due to season changes (winter shows less people than in summer)
    It will then be used by the program in order to determine the overal yearly afluence pattern within the expected restaurant, which in turns, can be converted into a number of expected clients at any given moment of the year.

The file distrib_setup_r1.json:
    Daily influences are obtained after my visual inspection of the google map data for the popular times for the restaurant:
    "Jap's table" at 245 Abercrombie St, Darlington NSW 2008, Australia
    Because there is no data for the morning, but that we plan to open on mornings, I extrapolated a bit.
