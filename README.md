# Geocode Address Collector

This is an address collector script that takes a `.txt` file of [what are 
assumed to be] unique addresses, uses Nominatim to geocode the addresses, 
and creates a CSV containing the original raw address, the geocoded address, 
the latitude, and the longitude

## Usage

To run, simply run `geocode_address_collector.py`, however it is **strongly recommended** to name a user agent when running this script (e.g., `geocode_address_collector.py check`). Read the footnotes under the **Restrictions** heading to see why.

This script was developed using `anaconda3-2021.11`, with Python 3.9.19. While it will probably work with any version of Python 3.9 or higher that has all the correct packages installed, I cannot guarantee that it will.

## Restrictions

This script uses [Nominatim](https://wiki.openstreetmap.org/wiki/Nominatim), a service provided by [OpenStreetMap](https://www.openstreetmap.org/), who deserve all the credit for making this script possible.

OpenStreetMap has a usage policy for Nominatim, which you should review [here](https://operations.osmfoundation.org/policies/nominatim/), but here are the highlights (as of June 18, 2024, footnotes are mine):

- No heavy uses (an absolute maximum of 1 request per second).[^a]
- Provide a valid HTTP Referer or User-Agent identifying the application (stock User-Agents as set by http libraries will not do).[^b]
- Clearly display [attribution](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines) as suitable for your medium.
- Data is provided under the [ODbL](https://www.openstreetmap.org/copyright) license which requires to share alike (although small extractions are likely to be covered by fair usage / fair dealing).

What this basically boils down to, according to my interpretation, is don't get greedy, give credit where it is due, 

[^a]: This is why the method `geocode_addresses()` has the line `time.sleep(1.1)`. **DO NOT** make it lower than 1 second.
[^b]: There is a default `user_agent` value in the application, but I strongly recommend including your own as an argument when running the script (See **Usage**).

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

This script is covered by the [MIT](https://choosealicense.com/licenses/mit/) license, but any use of data coming from OpenStreetMap (i.e., geocoded addresses that this script produces) is covered by the [ODbL](https://www.openstreetmap.org/copyright).