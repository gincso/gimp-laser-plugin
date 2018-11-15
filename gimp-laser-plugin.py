#!/usr/bin/python2

import sys
import math
from gimpfu import *


def laser_power(min, max, pixVal, intensity):
  if pixVal == 0xff: return 0
  return min + (max - min) * (255 - pixVal) * intensity / 25500


def distance(x1, y1, x2, y2):
  return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))


def image_to_gcode(timg, drawable, filename, outWidth, pixSize, feedRate,
                   minPower, maxPower, minRapid, intensity) :
  width = int(outWidth / pixSize)
  height = int(timg.height * width / timg.width)

  timg = pdb.gimp_image_duplicate(timg)
  pdb.gimp_image_scale(timg, width, height)

  # Flatten image so that we handle alpha channel correctly
  pdb.gimp_context_push()
  pdb.gimp_context_set_background((255, 255, 255))
  pdb.gimp_image_flatten(timg)
  pdb.gimp_context_pop()

  pdb.gimp_image_convert_grayscale(timg)

  drawable = pdb.gimp_image_get_active_drawable(timg)

  pdb.gimp_progress_init('Generating GCode...', None)

  with open(filename, 'w+') as f:
    f.write('G21 G90\nM3 F%d\n' % feedRate)

    forward = True
    lastX = lastY = None

    for row in range(drawable.height):
      y = row
      lastPixel = None

      pdb.gimp_progress_update(float(row) / drawable.height)

      for col in range(drawable.width):
        x = col if forward else (drawable.width - col - 1)
        pixel = drawable.get_pixel(x, y)[0]
        end = col == drawable.width - 1

        if col and pixel != lastPixel or end:
          power = laser_power(minPower, maxPower, lastPixel, intensity)
          rapid = lastPixel == 0xff

          if not end or not rapid:
            if rapid and lastX is not None:
              dist = distance(x, y, lastX, lastY) * pixSize
              if dist < minRapid: rapid = False

            lastX = x
            lastY = y

            f.write('G%d X%0.2f Y%0.2f S%d\n' % (
              0 if rapid else 1, x * pixSize, y * pixSize, power))

        lastPixel = pixel

      forward = not forward

    f.write('M5 S0\n')

    pdb.gimp_image_delete(timg)
    pdb.gimp_progress_end()


register(
  'Buildbotics_Laser_Engraving_Tool',
  'Laser engraving by Buildbotics\nCheck us out at buildbotics.com!',
  'Converts image to g-code for laser engraving',
  'Doug Coffland',
  'Doug Coffland',
  '2018',
  '<Image>/File/Export/Export g-code for laser engraving...',
  '*',
  [
    (PF_FILE,   'filename',  'Output file path name', 'out.gc'),
    (PF_FLOAT,  'outWidth',  'Output image width (mm)', 100),
    (PF_FLOAT,  'pixSize',   'Size of one output pixel (mm)', 0.25),
    (PF_FLOAT,  'feedRate',  'Feed rate in mm/minute', 3000),
    (PF_INT,    'minPower',  'Mimimum LASER S-value', 0),
    (PF_INT,    'maxPower',  'Maximum LASER S-value', 255),
    (PF_FLOAT,  'minRapid',  'Minimum rapid distance (mm)', 10),
    (PF_SLIDER, 'intensity', 'Laser intensity (%)', 100, [0, 100, 1]),
  ],
  [],
  image_to_gcode
)


main()