nano /etc/samba/smb.conf

[SharedDrive]
path = /home/pi/shared
browseable = yes
writeable = yes
create mask = 0777
directory mask = 0777
public = yes


mkdir -p /home/pi/shared
chmod 777 /home/pi/shared

sudo systemctl restart smbd

visit

smb://<raspberry_pi_ip>/SharedDrive
