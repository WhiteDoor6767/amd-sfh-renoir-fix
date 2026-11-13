obj-m += amd_sfh.o
amd_sfh-objs := amd_sfh_hid.o \
                amd_sfh_client.o \
                amd_sfh_pcie.o \
                hid_descriptor/amd_sfh_hid_desc.o \
                sfh1_1/amd_sfh_init.o \
                sfh1_1/amd_sfh_interface.o \
                sfh1_1/amd_sfh_desc.o

ccflags-y += -I$(src) -I$(src)/hid_descriptor -I$(src)/sfh1_1

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

default:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
