#!/usr/bin/expect -f

set timeout -1
spawn sh /app/esa-snap_all_unix_7_0.sh
expect "OK \\\[o, Enter\\\], Cancel \\\[c\\\]" 
send "\n"

expect "Yes, try deleting all SNAP user data \\\[1\\\], Delete only SNAP-internal configuration data (recommended). \\\[2, Enter\\\]" 
send "\n"

expect "\\\[/usr/local/snap\\\]" 
send "/app/snap\n"
    
expect "\\\[2,3,4,5,6,7\\\]" 
send "\n"

# python install
expect "Yes \\\[y, Enter\\\], No \\\[n\\\]" 
send "\n"

expect "\\\[/usr/local/bin\\\]" 
send "\n"

expect "Yes \\\[y\\\], No \\\[n, Enter\\\]" 
send "n\n"

expect "Yes \\\[y, Enter\\\], No \\\[n\\\]" 
send "n\n"

expect eof


