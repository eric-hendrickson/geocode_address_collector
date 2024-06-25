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
        with open(csv_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
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
            csv_file.close()
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

def geocode_addresses(
        unique_addresses,
        csv_path, no_geocodes_path,
        user_agent='check', break_time=1.1):
    percentage_bar_width = os.get_terminal_size().columns - 12
    rows_with_data = []
    rows_with_no_data = []
    if os.path.exists(no_geocodes_path):
        os.remove(no_geocodes_path)
    number_of_addresses = len(unique_addresses)
    geocoded_rows_written = 0
    non_geocodable_rows_written = 0
    app = Nominatim(user_agent=user_agent)
    for index, address in enumerate(unique_addresses):
        percentage = 100 * index / number_of_addresses
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
                rows_with_data.append(row)
            else:
                row = address
                rows_with_no_data.append(row)
            sys.stdout.write(
                "[{:{}}] {:.2f}%".format(
                    "=" * math.ceil(percentage),
                    percentage_bar_width - 1,
                    percentage
                )
            )
            # sys.stdout.flush()
            csv_file = open(csv_path, 'a')
            no_geocodes_file = open(no_geocodes_path, 'a')
            time_end = time.time() + break_time
            while time.time() < time_end:
                if len(rows_with_data) > 0:
                    csv_writer = csv.writer(csv_file, delimiter=',')
                    for row in rows_with_data:
                        csv_writer.writerow(row)
                        rows_with_data.remove(row)
                        geocoded_rows_written += 1
                if len(rows_with_no_data) > 0:
                    for row in rows_with_no_data:
                        no_geocodes_file.write("%s\n" % row)
                        rows_with_no_data.remove(row)
                        non_geocodable_rows_written += 1
            csv_file.close()
            no_geocodes_file.close()
        except KeyboardInterrupt:
            sys.exit(
                '\nCtrl+C detected, geocoding stopping. ' + \
                'You\'re going to have to run ' + \
                'this script again, but at least you stored some rows.'
            )
        except Exception as e:
            print(e)
            print(
                '\nWARNING: Incomplete. You\'re going to have to run ' + \
                'this script again, but at least you stored some rows.'
            )
            break
    return (
        rows_with_data,
        rows_with_no_data,
        geocoded_rows_written,
        non_geocodable_rows_written
    )

def completed_geocode_message_string(
        num_addresses_with_data,
        num_addresses_without_data,
        csv_path, no_geocodes_path):
    geocoded_address = 'address ' \
        if num_addresses_with_data == 1 else 'addresses '
    non_geocoded_address = 'address ' \
        if num_addresses_without_data == 1 else 'addresses '
    return '\nCompleted geocoding. Wrote ' + str(num_addresses_with_data) + \
        ' geocoded ' + geocoded_address + 'to `' + csv_path + '` and ' + \
        str(num_addresses_without_data) + ' ' + non_geocoded_address + \
        'that could not be geocoded to `' + no_geocodes_path + '`.'

def main(argv):
    time_start = time.time()

    # Nominatim user agent
    user_agent = 'check' if len(argv) == 0 else argv[0]
    # Unique addresses txt path
    txt_path = 'unique_addresses.txt'
    # Geocoded csv addresses path
    csv_path = 'geocoded_addresses.csv'
    # TXT file of addresses that couldn't be geocoded
    no_geocodes_path = 'no_geocodes.txt'
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
    
    # print('Checking `' + csv_path + '`...')
    # checking_geocode_addresses(unique_addresses, csv_path)
    
    print('Starting to geocode addresses...')
    with open(csv_path, 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(csv_headers)
        csv_file.close()
    rows_with_data, rows_with_no_data, geocoded_rows_written, non_geocodable_rows_written = geocode_addresses(
        unique_addresses, csv_path, no_geocodes_path, user_agent
    )
    
    # Completed geocoding and writing remaining values to csv and
    # addresses without geodata file
    with open(csv_path, 'a') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for row in rows_with_data:
            csv_writer.writerow(row)
            geocoded_rows_written += 1
        csv_file.close()
    with open(no_geocodes_path, 'a') as no_geocodes_file:
        for row in rows_with_no_data:
            no_geocodes_file.write("%s\n" % row)
            non_geocodable_rows_written += 1
        no_geocodes_file.close()
    
    # Completed geocoding and writing to file message
    print(
        completed_geocode_message_string(
            geocoded_rows_written,
            non_geocodable_rows_written,
            csv_path,
            no_geocodes_path
        )
    )

    print('Program took ' + str(time.time() - time_start) + ' seconds to complete.')


if __name__ == '__main__':
    main(sys.argv[1:])