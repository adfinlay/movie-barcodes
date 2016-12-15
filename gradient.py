from PIL import Image
import argparse
import os
import sys

parser = argparse.ArgumentParser(description='Adds gradient to an image.')
parser.add_argument('infile', help='Image file to be processed.')
parser.add_argument('outfile', nargs='?', help='File to save new image to.')
parser.add_argument('--gradient', help='Gradient of the gradient (defualt 3.).', type=float, default=3.)
parser.add_argument('--initial_opacity', help='Initial gradient opacity (default 1.).', type=float, default=1.)
args = parser.parse_args();

if not os.path.exists(args.infile):
    parser.error('Input file {} does not exist.'.format(args.infile))

if args.outfile and os.path.exists(args.outfile):
    parser.error('Output file {} already exists.'.format(args.outfile))

scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
outfile = args.outfile if args.outfile else os.path.join(scriptdir, 'gradient', os.path.split(args.infile)[1])

if not os.path.isdir(os.path.dirname(outfile)):
    os.mkdir(os.path.dirname(outfile))

def apply_black_gradient(path_in, path_out='out.png',
                         gradient=1., initial_opacity=1.):
    """
    Applies a black gradient to the image, going from left to right.

    Arguments:
    ---------
        path_in: string
            path to image to apply gradient to
        path_out: string (default 'out.png')
            path to save result to
        gradient: float (default 1.)
            gradient of the gradient; should be non-negative;
            if gradient = 0., the image is black;
            if gradient = 1., the gradient smoothly varies over the full width;
            if gradient > 1., the gradient terminates before the end of the width;
        initial_opacity: float (default 1.)
            scales the initial opacity of the gradient (i.e. on the far left of the image);
            should be between 0. and 1.; values between 0.9-1. give good results
    """

    # get image to operate on
    input_im = Image.open(path_in)
    if input_im.mode != 'RGBA':
        input_im = input_im.convert('RGBA')
    width, height = input_im.size

    # create a gradient that
    # starts at full opacity * initial_value
    # decrements opacity by gradient * x / width
    alpha_gradient = Image.new('L', (1, height), color=0xFF)
    for y in range(height):
        pos = y if y < height / 2. else height - y
        a = int((initial_opacity * 255.) * (1. - gradient * float(pos)/height))
        if a > 0:
            alpha_gradient.putpixel((0, y), a)
        else:
            alpha_gradient.putpixel((0, y), 0)
        # print '{}, {:.2f}, {}'.format(x, float(x) / width, a)
    alpha = alpha_gradient.resize(input_im.size)

    # create black image, apply gradient
    black_im = Image.new('RGBA', (width, height), color=0) # i.e. black
    black_im.putalpha(alpha)

    # make composite with original image
    output_im = Image.alpha_composite(input_im, black_im)
    output_im.save(path_out, 'PNG')

    return

apply_black_gradient(args.infile, outfile, args.gradient, args.initial_opacity)
