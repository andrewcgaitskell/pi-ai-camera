    nano /etc/samba/smb.conf
    
    [SharedDrive]
    path = /home/pi/shared
    browseable = yes
    writeable = yes
    create mask = 0777
    directory mask = 0777
    public = no

    sudo??????????
    
    mkdir -p /home/pi/shared
    chmod 777 /home/pi/shared
    chown pi:pi /home/pi/shared

    smbpasswd -a <USERNAME>
    
    systemctl restart smbd

    hostname -I
    
    then visit
    
    smb://<raspberry_pi_ip>/SharedDrive
