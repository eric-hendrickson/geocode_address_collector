import csv
import time
import sys
import os
import math
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def do_geocode(app, address, attempt=1, max_attempts=5):
    try:
        return app.geocode(address, timeout=30)
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return do_geocode(address, attempt=attempt+1)
        raise

def unique_addresses_message_string(num):
    to_be = 'is ' if num == 1 else 'are '
    address = 'address ' if num == 1 else 'addresses '
    segment = 'This means there ' + to_be + str(num) + ' unique '
    return segment + address + 'to write.'

def csv_addresses_string(csv_num, no_geographic_num, unique_num, csv_path):
    to_be = 'is ' if csv_num == 1 else 'are '
    address = ' address ' if csv_num == 1 else ' addresses '
    segment = 'There ' + to_be + str(csv_num) + address + 'in `'
    segment += csv_path + '`, including ' + str(no_geographic_num) + ' with '
    segment += 'no geographic data. '
    return segment + unique_addresses_message_string(unique_num)

def checking_geocode_addresses(unique_addresses, csv_path):
    number_csv_addresses = 0
    number_no_geographic_data = 0
    if os.path.isfile(csv_path):
        with open(csv_path, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for index, row in enumerate(csv_reader):
                if index == 0:
                    continue
                raw_address = row[0]
                no_geographical_data = \
                    row[1] == 'None' or row[2] == 'None' or row[3] == 'None'
                if no_geographical_data:
                    number_no_geographic_data += 1
                    if raw_address not in unique_addresses:
                        unique_addresses.append(raw_address)
                else:
                    while raw_address in unique_addresses:
                        unique_addresses.remove(raw_address)
                number_csv_addresses += 1
            csvfile.close()
        print(
            csv_addresses_string(
                number_csv_addresses,
                number_no_geographic_data,
                len(unique_addresses),
                csv_path
            )
        )
    else:
        print(
            'File not present. ' + \
            unique_addresses_message_string(len(unique_addresses))
        )

def geocode_addresses(unique_addresses, user_agent='check'):
    percentage_bar_width = os.get_terminal_size().columns - 10
    rows = []
    app = Nominatim(user_agent=user_agent)
    for index, address in enumerate(unique_addresses):
        percentage = 100 * index / len(unique_addresses)
        sys.stdout.write('\r')
        try:
            location = do_geocode(app, address)
            if (location):
                row = \
                    [
                        address,
                        location.address,
                        location.latitude,
                        location.longitude
                    ]
                rows.append(row)
            else:
                row = [address, None, None, None]
                rows.append(row)
            sys.stdout.write(
                "[{:{}}] {:.2f}%".format(
                    "=" * math.ceil(percentage),
                    percentage_bar_width - 1,
                    percentage
                )
            )
            sys.stdout.flush()
            time.sleep(1.1)
        except KeyboardInterrupt:
            sys.exit(
                '\nCtrl+C detected, geocoding stopping. ' + \
                'Nothing should have been stored.'
            )
        except Exception as e:
            print(e)
            print(
                '\nWARNING: Incomplete. You\'re going to have to run ' + \
                'this script again, but at least you\'ll store some rows.'
            )
            break
    return rows

def completed_geocode_message_string(num, filename):
    address = 'address ' if num == 1 else 'addresses '
    return '\nCompleted geocoding. Writing ' + str(num) + \
        ' geocoded ' + address + 'to `' + filename + '`...'

def main(argv):
    try:
        # Nominatim user agent
        user_agent = 'check' if len(argv) == 0 else argv[0]
        # Unique addresses txt path
        txt_path = 'unique_addresses.txt'
        # Geocoded csv addresses path
        csv_path = 'geocoded_addresses.csv'
        # Written csv headers
        csv_headers = [
            'residential_address',
            'geocoded_address',
            'latitude',
            'longitude'
        ]

        print('Opening `' + txt_path + '`...')
        unique_addresses = []
        with open(txt_path) as file:
            for line in file:
                unique_addresses.append(line.strip())

        print(
            'Total number of addresses in `' + txt_path + '`: ' + \
            str(len(unique_addresses))
        )
        
        print('Checking `' + csv_path + '`...')
        checking_geocode_addresses(unique_addresses, csv_path)
        
        print('Starting to geocode addresses...')
        geocoded_rows = geocode_addresses(unique_addresses, user_agent)
        
        # Completed geocoding and writing to csv
        print(
            completed_geocode_message_string(
                len(geocoded_rows), csv_path
            )
        )
        with open(csv_path, 'w') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            csv_writer.writerow(csv_headers)
            for row in geocoded_rows:
                csv_writer.writerow(row)
            csvfile.close()

        print('Finished writing to `' + csv_path + '`.')
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main(sys.argv[1:])