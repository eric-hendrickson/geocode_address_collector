import csv
import itertools
import time
import sys
import os
from collections import defaultdict
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def do_geocode(app, address, attempt=1, max_attempts=5):
    try:
        return app.geocode(address, timeout=30, addressdetails=True)
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return do_geocode(address, attempt=attempt+1)
        raise

def to_be(num):
    return 'is' if num == 1 else 'are'

def address(num):
    return 'address' if num == 1 else 'addresses'

def unique_addresses_message_string(num):
    return 'This means there {} {} unique {} to write.'.format(
        to_be(num), num, address(num)
    )

def csv_addresses_string(csv_num, no_geographic_num, unique_num, geocoded_path):
    return 'There {} {} {} in `{}`. {}'.format(
        to_be(csv_num),
        csv_num,
        address(csv_num),
        geocoded_path,
        unique_addresses_message_string(unique_num)
    )

def lower_first(iterator):
    return itertools.chain([next(iterator).lower()], iterator)

def compare_address_content(dict1, dict2):
    for index in dict1:
        if dict1.get(index) != dict2.get(index):
            return False
    return 

# TODO: Find a way to get this functionality back with respect to the new lists of dicts
# approach we are now using
# def checking_geocode_addresses(unique_addresses, written_csv_headers, geocoded_path):
#     number_csv_addresses = 0
#     number_no_geographic_data = 0
#     if os.path.isfile(geocoded_path):
#         with open(geocoded_path, 'r') as csv_file:
#             read_dict = csv.DictReader(lower_first(csv_file))
#             for row in read_dict:
#                 print(row)
#                 while raw_address in unique_addresses:
#                     unique_addresses.remove(raw_address)
#                     number_csv_addresses += 1
#         print(
#             csv_addresses_string(
#                 number_csv_addresses,
#                 number_no_geographic_data,
#                 len(unique_addresses),
#                 geocoded_path
#             )
#         )
#     else:
#         print(
#             'File not present. {}'.format(
#                 unique_addresses_message_string(len(unique_addresses))
#             )
#         )
#         print('Creating `{}` now.'.format(geocoded_path))
#         with open(geocoded_path, 'w') as csv_file:
#             csv_writer = csv.writer(csv_file, delimiter=',')
#             csv_writer.writerow(written_csv_headers)

def update_percentage_bar(index, num_unique_addresses):
    percentage_bar_width = os.get_terminal_size().columns - 10
    bar_multiplier = index / num_unique_addresses

    percentage = 100 if index == num_unique_addresses - 1 \
        else bar_multiplier * 100
    number_of_bars = bar_multiplier * percentage_bar_width
    progress_width = 1 if number_of_bars < 1 else round(number_of_bars)

    sys.stdout.write('\r')
    sys.stdout.write(
        "[{:{}}] {:5.2f}%".format(
            "=" * progress_width,
            percentage_bar_width - 1,
            percentage
        )
    )
    sys.stdout.flush()

def write_to_csv(rows, rows_written, path, headers):
    check = os.path.exists(path)
    with open(path, 'a') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        if not check:
            csv_writer.writerow(headers)
        for row in rows:
            csv_writer.writerow(row)
            rows.remove(row)
            rows_written += 1
    return rows_written

def geocode_addresses(
        unique_addresses, geocoded_path, partially_geocoded_path,
        no_geocodes_path, read_csv_headers, written_csv_headers,
        user_agent='check', precision='house_number', break_time=1.1):
    app = Nominatim(user_agent=user_agent)
    warning_string = 'You\'re going to have to run this script again.'
    rows_with_data = []
    rows_with_incomplete_data = []
    rows_without_data = []
    geocoded_rows_written = 0
    partially_geocoded_rows_written = 0
    non_geocodable_rows_written = 0
    for index, address in enumerate(unique_addresses):     
        try:
            # Get geocoded location
            location = do_geocode(app, address)
            if (location):
                address_details = location.raw.get('address', {})
                precise = address_details.get(precision, False)
                if (precision == None or precise):
                    row = \
                        [
                            address['street'],
                            address['city'],
                            address['state'],
                            address['zip'],
                            str(address_details),
                            location.latitude,
                            location.longitude
                        ]
                    rows_with_data.append(row)
                else:
                    row = \
                        [
                            address['street'],
                            address['city'],
                            address['state'],
                            address['zip'],
                            str(address_details),
                            location.latitude,
                            location.longitude
                        ]
                    rows_with_incomplete_data.append(row)
            else:
                row = \
                    [
                        address['street'],
                        address['city'],
                        address['state'],
                        address['zip']
                    ]
                rows_without_data.append(row)
            
            # Update percentage bar
            update_percentage_bar(index, len(unique_addresses))

            # While waiting, write to file
            time_end = time.time() + break_time
            while time.time() < time_end:
                if len(rows_with_data) > 0:
                    geocoded_rows_written = write_to_csv(
                        rows_with_data,
                        geocoded_rows_written,
                        geocoded_path,
                        written_csv_headers
                    )
                if len(rows_with_incomplete_data) > 0:
                    partially_geocoded_rows_written = write_to_csv(
                        rows_with_incomplete_data,
                        partially_geocoded_rows_written,
                        partially_geocoded_path,
                        written_csv_headers
                    )
                if len(rows_without_data) > 0:
                    non_geocodable_rows_written = write_to_csv(
                        rows_without_data,
                        non_geocodable_rows_written,
                        no_geocodes_path,
                        read_csv_headers
                    )    
        except KeyboardInterrupt:
            sys.exit(
                '\nCtrl+C detected, geocoding stopping. {}'.format(
                    warning_string
                )
            )
        except Exception as e:
            print('\n{}\n{}'.format(e, warning_string))
            break
    return (
        rows_with_data,
        rows_with_incomplete_data,
        rows_without_data,
        geocoded_rows_written,
        partially_geocoded_rows_written,
        non_geocodable_rows_written
    )

def completed_geocode_message_string(
        num_addresses_with_data,
        num_addresses_with_partial_data,
        num_addresses_without_data,
        geocoded_path, partially_geocoded_path, no_geocodes_path):
    return '\nCompleted geocoding. Wrote {} geocoded {} to `{}`, '.format(
        num_addresses_with_data, address(num_addresses_with_data), geocoded_path
    ) + '{} {} with partial geocoded data to {}, and '.format(
        num_addresses_with_partial_data,
        address(num_addresses_with_partial_data),
        partially_geocoded_path
    ) + '{} {} that could not be geocoded to `{}`.'.format(
        num_addresses_without_data,
        address(num_addresses_without_data),
        no_geocodes_path
    )

def main(argv):
    time_start = time.time()

    # Nominatim user agent
    user_agent = 'check' if len(argv) == 0 else argv[0]
    # Unique addresses txt path
    unique_addresses_path = 'unique_addresses.csv'
    # Geocoded csv addresses path
    geocoded_path = 'geocoded_addresses.csv'
    # Partially geocoded csv addresses path
    partially_geocoded_path = 'partially_geocoded_addresses.csv'
    # TXT file of addresses that couldn't be geocoded
    no_geocodes_path = 'no_geocodes.csv'
    # Read csv headers
    read_csv_headers = [
        'Street',
        'City',
        'State',
        'ZIP'
    ]
    # Written csv headers
    written_csv_headers = [
        'Street',
        'City',
        'State',
        'ZIP',
        'latitude',
        'longitude'
    ]

    # Opening unique addresses txt file
    print('Opening `{}`...'.format(unique_addresses_path))
    # If the unique addresses txt file does not exist, we're going to have to exit
    if not os.path.exists(unique_addresses_path):
        sys.exit(
            'File does not exist, therefore no addresses can be geocoded.'
        )
    unique_addresses = []
    with open(unique_addresses_path) as file:
        read_dict = csv.DictReader(lower_first(file))
        fieldnames = read_dict.fieldnames
        for field in read_csv_headers:
            if field.lower() not in fieldnames:
                sys.exit(
                    'File does not have correct headers, therefore no '+ \
                    'addresses can be geocoded.'
                )
        for row in read_dict:
            unique_addresses.append(row)

    # Number of addresses in unique addresses file
    print(
        'Total number of addresses in `{}`: {}'.format(
            unique_addresses_path, str(len(unique_addresses))
        )
    )
    
    # Clean up files
    # print('Checking `{}`...'.format(geocoded_path))
    # checking_geocode_addresses(
    #     unique_addresses, written_csv_headers, geocoded_path
    # )
    if os.path.exists(geocoded_path):
        os.remove(geocoded_path)
    if os.path.exists(partially_geocoded_path):
        os.remove(partially_geocoded_path)
    if os.path.exists(no_geocodes_path):
        os.remove(no_geocodes_path)
    
    print('Starting to geocode addresses...')
    rows_with_data, rows_with_incomplete_data, rows_without_data, \
    geocoded_rows_written, partially_geocoded_rows_written, \
    non_geocodable_rows_written = \
        geocode_addresses(
            unique_addresses, geocoded_path, partially_geocoded_path,
            no_geocodes_path, read_csv_headers, written_csv_headers, user_agent
        )
    
    # Completed geocoding and writing remaining values to csv and
    # addresses without geodata file
    geocoded_rows_written = write_to_csv(
        rows_with_data,
        geocoded_rows_written,
        geocoded_path,
        written_csv_headers
    )
    partially_geocoded_rows_written = write_to_csv(
        rows_with_incomplete_data,
        partially_geocoded_rows_written,
        partially_geocoded_path,
        written_csv_headers
    )
    non_geocodable_rows_written = write_to_csv(
        rows_without_data, non_geocodable_rows_written,
        no_geocodes_path, read_csv_headers
    )  
    
    # Completed geocoding and writing to file message
    print(
        completed_geocode_message_string(
            geocoded_rows_written,
            partially_geocoded_rows_written,
            non_geocodable_rows_written,
            geocoded_path,
            partially_geocoded_path,
            no_geocodes_path
        )
    )

    print('Program took {:.3f} seconds to complete'.format(
        time.time() - time_start
    ))
    print('(Time ended: {})'.format(
        datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
    ))

if __name__ == '__main__':
    main(sys.argv[1:])