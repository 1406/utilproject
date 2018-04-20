# mainwindow
## component
- background
- oem
- stage
- power
- settings
- logout

## callback
- set oem
- show stage
- hide stage
- show power conf
- show settings
- logout

# desktop
## component
- desktop icon
- operate list

## callback
- show operate list
- hide operate list

### desk
- cache desktop
- run desktop
- snapshot
- localdisk
- monitor
- delete
- restore
- poweroff

### image
- download src
- run image (create/modify)
- upload
- delete
- resotre
- poweroff

## object
1. desktop
2. image

# logindialog
## component
- oem
- user/admin/guest
- username
- password
- autologin checkbox
- ok

## callback
- login
- manager login
- guest login
- set autologin

# listdialog
## component
- title
- new button
- button list
- ok/cancel

## callback
- new snapshot
- new localdisk
- new desktop
- show snapshot operate
- show localdisk operate
- set monitor
- cache desktop
- show systemconfig
- set resolution
- exchange monitor
- show change password
- show regist
- show about

## object
1. snapshot list (new)
2. snapshot operate
3. localdisk list (new)
4. localdisk operate
5. monitor list
6. desktop list (new)
7. desktop list
8. system config

# snapshot create
## component
- title
- name
- description
- ok/cancel

## callback
- create snapshot

# localdisk create
## component
- title
- label
- size
- block device
- ok/cancel

## callback
- create localdisk

# desktop create 1~3
## component
- title
- stacked widget
- ok/cancel

### page 1
- subtitle
- name
- restore rule...

### page 2
- subtitle
- image
- network...
- vcpu
- memory
- display
- localdisk...

### page 3
- software...

# question box
## component
- title
- quertion
- ok/cancel

1. reboot
2. poweroff
3. poweroff (no cancel)
4. generate question

# about
## component
- title
- version
- cpu
- memory
- harddisk
- mac, ip * n
- ok

# resolution dialog
## component
- title
- resolution combo
- ok/cancel

# password dialog
## component
- title
- username
- old password
- new password
- new 2
- ok/cancel

# regist dialog
## component
- title
- server ip
- host name
- static ip checkbox
- host ip
- netmask
- gateway
- ok/cancel

# message box
## component
- title
- message
- ok

1. generate message
2. lock screen (no ok)

# progress
## component
- title
- message
- wating flash
- progress bar
- detail