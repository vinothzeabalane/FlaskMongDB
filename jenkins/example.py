filename = 'lm-302-05-s2-4TB-EB0-2024-08-06'
# filename = 'lm-302-17-s2-8TB-SPI-2024-08-06'

# parts = filename.split('-')

# if 'SPI' in parts:
#     spiflow = True
#     eb0flow = False

# else:
#     spiflow = False
#     eb0flow = True

fparts = filename.split('-')
spiflow = 'SPI' in fparts
eb0flow = not spiflow


print (spiflow, eb0flow)