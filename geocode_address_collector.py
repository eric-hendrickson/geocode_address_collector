import csv
import time
import sys
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def do_geocode(app, address, attempt=1, max_attempts=5):
    try:
        return app.geocode(address, timeout=30)
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

def csv_addresses_string(csv_num, no_geographic_num, unique_num, csv_path):
    return 'There {} {} {} in `{}`. {}'.format(
        to_be(csv_num),
        csv_num,
        address(csv_num),
        csv_path,
        unique_addresses_message_string(unique_num)
    )

def checking_geocode_addresses(unique_addresses, csv_headers, csv_path):
    number_csv_addresses = 0
    number_no_geographic_data = 0
    if os.path.isfile(csv_path):
        with open(csv_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for index, row in enumerate(csv_reader):
                if index == 0:
                    continue
                raw_address = row[0]
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
            'File not present. {}'.format(
                unique_addresses_message_string(len(unique_addresses))
            )
        )
        print('Creating `{}` now.'.format(csv_path))
        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',')
            csv_writer.writerow(csv_headers)

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

def write_to_geocoded_addresses(
        rows_with_data, geocoded_rows_written, csv_path):
    with open(csv_path, 'a') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for row in rows_with_data:
            csv_writer.writerow(row)
            rows_with_data.remove(row)
            geocoded_rows_written += 1
    return geocoded_rows_written

def write_to_no_geocodes(
        rows_without_data, non_geocodable_rows_written, no_geocodes_path):
    with open(no_geocodes_path, 'a') as no_geocodes_file:
        for row in rows_without_data:
            no_geocodes_file.write("%s\n" % row)
            rows_without_data.remove(row)
            non_geocodable_rows_written += 1
    return non_geocodable_rows_written

def geocode_addresses(
        unique_addresses,
        csv_path, no_geocodes_path,
        user_agent='check', break_time=1.1):
    app = Nominatim(user_agent=user_agent)
    warning_string = 'You\'re going to have to run this script again, ' + \
        'but at least you stored some rows.'
    rows_with_data = []
    rows_without_data = []
    geocoded_rows_written = 0
    non_geocodable_rows_written = 0
    for index, address in enumerate(unique_addresses):        
        try:
            # Get geocoded location
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
                rows_without_data.append('%s' % address)
            
            # Update percentage bar
            update_percentage_bar(index, len(unique_addresses))

            # While waiting, write to file
            time_end = time.time() + break_time
            while time.time() < time_end:
                if len(rows_with_data) > 0:
                    geocoded_rows_written = write_to_geocoded_addresses(
                        rows_with_data, geocoded_rows_written, csv_file
                    )
                if len(rows_without_data) > 0:
                    non_geocodable_rows_written = write_to_no_geocodes(
                        rows_without_data,
                        non_geocodable_rows_written,
                        no_geocodes_path
                    )    
        except KeyboardInterrupt:
            sys.exit(
                '\nCtrl+C detected, geocoding stopping. {}'.format(
                    warning_string()
                )
            )
        except Exception as e:
            print('{}\n{}'.format(e, warning_string()))
            break
    return (
        rows_with_data,
        rows_without_data,
        geocoded_rows_written,
        non_geocodable_rows_written
    )

def completed_geocode_message_string(
        num_addresses_with_data,
        num_addresses_without_data,
        csv_path, no_geocodes_path):
    return '\nCompleted geocoding. Wrote {} geocoded {} to `{}` and '.format(
        num_addresses_with_data, address(num_addresses_with_data), csv_path
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

    # Opening unique addresses txt file
    print('Opening `{}`...'.format(txt_path))
    # If the unique addresses txt file does not exist, we're going to have to exit
    if not os.path.exists(txt_path):
        sys.exit(
            'File does not exist, therefore no addresses can be geocoded.'
        )
    unique_addresses = []
    with open(txt_path) as file:
        for line in file:
            unique_addresses.append(line.strip())

    # Number of addresses in unique addresses file
    print(
        'Total number of addresses in `{}`: {}'.format(
            txt_path, str(len(unique_addresses))
        )
    )
    
    # Checking geocoded csv to see how many addresses have already been written
    print('Checking `{}`...'.format(csv_path))
    checking_geocode_addresses(unique_addresses, csv_headers, csv_path)
    if os.path.exists(no_geocodes_path):
        os.remove(no_geocodes_path)
    
    print('Starting to geocode addresses...')
    rows_with_data, rows_without_data, \
    geocoded_rows_written, non_geocodable_rows_written = \
        geocode_addresses(
            unique_addresses, csv_path, no_geocodes_path, user_agent
        )
    
    # Completed geocoding and writing remaining values to csv and
    # addresses without geodata file
    geocoded_rows_written = write_to_geocoded_addresses(
        rows_with_data, geocoded_rows_written, csv_path
    )
    non_geocodable_rows_written = write_to_no_geocodes(
        rows_without_data, non_geocodable_rows_written, no_geocodes_path
    )  
    
    # Completed geocoding and writing to file message
    print(
        completed_geocode_message_string(
            geocoded_rows_written,
            non_geocodable_rows_written,
            csv_path,
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