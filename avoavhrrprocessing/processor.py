"""
Create and deliver a volcview product.

This module provides utility functions and an abstract base class for
creating images for volcview.

"""

# import calendar
# import io
import json

# import os
import os.path
from abc import ABC

import aggdraw
import boto3

# from geotiepoints.multilinear_cython import multilinear_interpolation
from pydecorate import DecoratorAGG

# from pyresample import load_area
from satpy.dataset import combine_metadata

# from satpy.enhancements import piecewise_linear_stretch
from satpy.scene import Scene

# from satpy.utils import debug_on, debug_off
from satpy.writers import add_overlay
from trollimage import colormap
from trollimage.xrimage import XRImage

from . import parse_filename

# from satpy import find_files_and_readers


# import pyspectral
# import requests


# from trollsched.satpass import Pass

GOLDENROD = (218, 165, 32)
TYPEFACE = "/mnt/rsdata/Cousine-Bold.ttf"
FONT_SIZE = 14
COAST_DIR = "/mnt/rsdata/gshhg"
AREA_DEF = "/mnt/rsdata/trollconfig/areas.def"
POST_TIMEOUT = 30
AVHRR_ROOT = os.environ["AVHRR_ROOT"]
AVHRR_PNG_TOPIC = os.environ["AVHRR_PNG_TOPIC"]
PNG_FILE_PREFIX = os.path.join(
    AVHRR_ROOT, "png/{date}/{sector}/{sector}-{platform}-{product}-{datet}.png"
)


def processor_factory(files):
    scene = Scene(filenames=files, reader="avhrr_l1b_aapp")
    platform = parse_filename(files[0])["platform"]
    for p in Processor.__subclasses__():
        print(f"File matched {p.product}")
        yield p(scene, platform)


class Processor(ABC):
    """Abstract superclass for processors

    I create and deliver products to volcview.

    Parameters
    ----------
    message : posttroll.message.Message
       The message to be processed.
    product : string
       The product to be created.
    product_label: string
       The product-specific portion of the labled shown on the volcview
       image.
    """

    product = None

    def __init__(self, scene, platform, product, dataset, volcview_band, product_label):
        # debug_on()
        self.product = product
        self.platform = platform
        self.dataset = dataset
        self.product_label = product_label
        self.volcview_band = volcview_band
        self.color_bar_font = aggdraw.Font(GOLDENROD, TYPEFACE, size=FONT_SIZE)
        self.scene = scene

        print(f"KEYS: {self.scene}")

    def load_data(self):
        """Load data into a scene
        """
        self.scene.load([self.dataset])

    def apply_colorbar(self, dcimg):
        """Apply a colorbar to an image.

        Parameters
        ----------
        dcimage : pydecorate.DecoratorAGG
            Image to receive colorbar
        """
        pass

    def enhance_image(self, img):
        """Apply enhancements to image data.

        Parameters
        ----------
        img : trollimage.xrimage.XRImage
            Image to be enhanced
        """
        pass

    def decorate_pilimg(self, pilimg):
        """Apply decorations to an image

        Parameters
        ----------
        pilimg : PIL.Image
        """
        dc = DecoratorAGG(pilimg)
        dc.align_bottom()

        self.apply_colorbar(dc)
        self.apply_label(dc)

    def draw_colorbar(self, dcimg, colors, tick_marks, minor_tick_marks):
        """Draw a colorbar on an image

        Parameters
        ----------
        dcimg : pydecorate.DecoratorAGG
            Image to receive colorbar
        colors
        tick_marks
        minor_tick_marks

        .. note:: This is typically called by a concrete apply_colorbar method.
        """
        dcimg.add_scale(
            colors,
            extend=True,
            tick_marks=tick_marks,
            minor_tick_marks=minor_tick_marks,
            font=self.color_bar_font,
            height=20,
            margins=[1, 1],
        )
        dcimg.new_line()

    def apply_label(self, dcimg):
        """Apply the standard text label to an image

        Parameters
        ----------
         dcimg : pydecorate.DecoratorAGG
            Image to label
        """
        start_string = self.scene.start_time.strftime("%m/%d/%Y %H:%M UTC")
        label = "{} {} AVHRR {}".format(start_string, self.platform, self.product_label)
        dcimg.add_text(
            label,
            font=TYPEFACE,
            height=30,
            extend=True,
            bg_opacity=128,
            bg="black",
            line=GOLDENROD,
            font_size=14,
        )

    def filename(self, sector_def):
        return PNG_FILE_PREFIX.format(
            date=self.scene.start_time.strftime("%Y%j"),
            sector=sector_def.area_id,
            product=self.product,
            platform="noaa18" if self.platform == "NOAA 18" else "noaa19",
            datet=self.scene.start_time.strftime("%Y%m%dT%H%M%SZ"),
        )

    def write_image(self, sector_def):
        try:
            local = self.scene.resample(
                destination=sector_def, radius_of_influence=5000
            )
        except ValueError as e:
            print("TOMP SAYS: not sure why this happens. Do something about it.")
            raise e

        img = XRImage(local[self.dataset].squeeze())
        self.enhance_image(img)
        print("enhanced resampled image")
        img = add_overlay(
            img, area=sector_def, coast_dir=COAST_DIR, color=GOLDENROD, fill_value=0
        )
        pilimg = img.pil_image()
        self.decorate_pilimg(pilimg)

        filename = self.filename(sector_def)
        filedir = os.path.dirname(filename)
        if not os.path.exists(filedir):
            print(f"Creating {dir}")
            os.makedirs(filedir)
        print(f"saving to {filename}")
        pilimg.save(filename, format="PNG")
        msg = {
            "file": filename,
            "area_id": sector_def.area_id,
            "product": self.product,
            "volcview_band": self.volcview_band,
            "start_time": self.scene.start_time.isoformat(),
        }
        print(f"Posting: {msg}")
        if AVHRR_PNG_TOPIC:
            boto3.client("sns").publish(
                TargetArn=AVHRR_PNG_TOPIC, Message=json.dumps(msg)
            )


class TIR(Processor):
    product = "TIR"

    def __init__(self, scene, platform):
        super().__init__(
            scene,
            platform,
            TIR.product,
            "4",
            "Thermal IR",
            "thermal infrared brightness tempeerature (c)",
        )

    def enhance_image(self, img):
        img.crude_stretch(208.15, 308.15)  # -65c - 35c
        img.invert()

    def apply_colorbar(self, dcimg):
        colors = colormap.greys
        colors.set_range(-65, 35)
        super().draw_colorbar(dcimg, colors, 20, 10)


class MIR(Processor):
    product = "MIR"

    def __init__(self, scene, platform):
        super().__init__(
            scene,
            platform,
            MIR.product,
            "3b",
            "Mid-IR",
            "mid-infrared brightness temperature (c)",
        )
        self.colors = colormap.Colormap(
            (0.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 1.0, 1.0))
        )  # NOQA: E501
        self.colors.set_range(-50, 50)

    def enhance_image(self, img):
        img.crude_stretch(223.15, 323.15)  # -50c - 50c

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 20, 10)


class BTD(Processor):
    product = "BTD"

    def __init__(self, scene, platform):
        super().__init__(
            scene,
            platform,
            BTD.product,
            "BTD",
            "TIR BTD",
            "brightness temperature difference",
        )
        self.color_bar_font = aggdraw.Font((0, 0, 0), TYPEFACE, size=14)
        self.colors = colormap.Colormap(
            (0.0, (0.5, 0.0, 0.0)),
            (0.071428, (1.0, 0.0, 0.0)),
            (0.142856, (1.0, 0.5, 0.0)),
            (0.214284, (1.0, 1.0, 0.0)),
            (0.285712, (0.5, 1.0, 0.5)),
            (0.357140, (0.0, 1.0, 1.0)),
            (0.428568, (0.0, 0.5, 1.0)),
            (0.499999, (0.0, 0.0, 1.0)),
            (0.5000, (0.5, 0.5, 0.5)),
            (1.0, (1.0, 1.0, 1.0)),
        )
        self.colors.set_range(-6, 5)

    def enhance_image(self, img):
        img.colorize(self.colors)

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 1, 0.5)

    def load_data(self):
        self.scene.load(["4", "5"])
        try:
            self.scene = self.scene.resample(resampler="native")
        except ValueError as e:
            print("TOMP SAYS: not sure why this happens. Do something about it.")
            raise e

        self.scene[self.dataset] = self.scene["4"] - self.scene["5"]
        self.scene[self.dataset].attrs = combine_metadata(
            self.scene["4"], self.scene["5"]
        )


class VIS(Processor):
    product = "VIS"

    def __init__(self, scene, platform):
        super().__init__(
            scene,
            platform,
            VIS.product,
            "1",
            "Visible",
            "visible reflectance (percent)",
        )  # NOQA: E501
        self.colors = colormap.Colormap(
            (0.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 1.0, 1.0))
        )  # NOQA: E501
        self.colors.set_range(0, 100)

    def apply_colorbar(self, dcimg):
        super().draw_colorbar(dcimg, self.colors, 20, 10)

    def enhance_image(self, img):
        img.crude_stretch()
