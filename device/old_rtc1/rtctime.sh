sudo timedatectl set-ntp true  
sudo systemctl restart systemd-timesyncd  
sleep 5  
sudo timedatectl set-local-rtc 0  
sudo hwclock --systohc --utc  
timedatectl status && hwclock -r
