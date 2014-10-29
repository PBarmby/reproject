# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np
from astropy.io.fits import PrimaryHDU, ImageHDU, Header
from astropy.wcs import WCS

from .wcs_utils import has_celestial


__all__ = ['reproject']

ORDER = {}
ORDER['nearest-neighbor'] = 0
ORDER['bilinear'] = 1
ORDER['biquadratic'] = 2
ORDER['bicubic']= 3


def reproject(input_data, output_projection, shape_out=None, projection_type='bilinear'):
    """
    Reproject data to a new projection.

    Parameters
    ----------
    input_data : `~astropy.io.fits.PrimaryHDU` or `~astropy.io.fits.ImageHDU` or tuple
        The input data to reproject. This can be an image HDU object from
        :mod:`astropy.io.fits`, such as a `~astropy.io.fits.PrimaryHDU`
        or `~astropy.io.fits.ImageHDU`, or it can be a tuple where the
        first element is a `~numpy.ndarray` and the second element is
        either a `~astropy.wcs.WCS` or a `~astropy.io.fits.Header` object
    output_projection : `~astropy.wcs.WCS` or `~astropy.io.fits.Header`
        The output projection, which can be either a `~astropy.wcs.WCS`
        or a `~astropy.io.fits.Header` instance.
    shape_out : tuple
        If ``output_projection`` is a `~astropy.wcs.WCS` instance, the
        shape of the output data should be specified separately.
    projection_type : str
        The reprojection type, which can be one of:
            * 'nearest-neighbor'
            * 'bilinear'
            * 'biquadratic'
            * 'bicubic'
            * 'flux-conserving'
            * 'deforest' (C.E. DeForest, Solar Physics 2004)

    Returns
    -------
    array_new : `~numpy.ndarray`
        The reprojected data
    footprint : `~numpy.ndarray`
        Footprint of the input array in the output array. Values of 0 indicate
        no coverage or valid values in the input image, while values of 1
        indicate valid values. Intermediate values indicate partial coverage.
    """

    if isinstance(input_data, (PrimaryHDU, ImageHDU)):
        array_in = input_data.data
        wcs_in = WCS(input_data.header)
    elif isinstance(input_data, tuple) and isinstance(input_data[0], np.ndarray):
        array_in = input_data[0]
        if isinstance(input_data[1], Header):
            wcs_in = WCS(input_data[1])
        else:
            wcs_in = input_data[1]
    else:
        raise TypeError("input_data should either be an HDU object or a tuple of (array, WCS) or (array, Header)")

    if isinstance(output_projection, Header):
        wcs_out = WCS(output_projection)
        try:
            shape_out = [output_projection['NAXIS{0}'.format(i+1)] for i in range(output_projection['NAXIS'])][::-1]
        except KeyError:
            if shape_out is None:
                raise ValueError("Need to specify shape since output header does not contain complete shape information")
    elif isinstance(output_projection, WCS):
        wcs_out = output_projection
        if shape_out is None:
            raise ValueError("Need to specify shape when specifying output_projection as WCS object")


    if projection_type in ORDER:

        order = ORDER[projection_type]

        # For now only celestial reprojection is supported
        if has_celestial(wcs_in):
            from .interpolation import reproject_celestial
            return reproject_celestial(array_in, wcs_in, wcs_out, shape_out=shape_out, order=order)
        else:
            raise NotImplementedError("Currently only data with a WCS that includes a celestial component can be reprojected")

    elif projection_type == 'deforest':

        # For now only celestial reprojection is supported
        if has_celestial(wcs_in):
            from .deforest import reproject_celestial
            return reproject_celestial(array_in, wcs_in, wcs_out, shape_out=shape_out)
        else:
            raise NotImplementedError("Currently only data with a WCS that includes a celestial component can be reprojected")

    elif projection_type == 'flux-conserving':

        # For now only 2-d celestial reprojection is supported
        if has_celestial(wcs_in) and wcs_in.naxis == 2:
            from .spherical_intersect import reproject_celestial
            return reproject_celestial(array_in, wcs_in, wcs_out, shape_out=shape_out)
        else:
            raise NotImplementedError("Currently only data with a 2-d celestial WCS can be reprojected using flux-conserving algorithm")

    else:
        raise ValueError("Unknown projection type: {0}".format(projection_type))
