import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
import os, h5py, yaml
import astropy.units as u
from astropy.io import fits

class ObjDict(dict):
    '''
    This is an abstract class for allowing the keys of a dictionary to be accessed like class attributes.
    '''

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: "+name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: "+name)

class WiseGuyError(Exception):
    pass

class CRISP:
    '''
    This is a class for CRISP data cubes to make it easy to plot and obtain spectral line profiles from the data.

    Parameters
    ----------
    files: str or list of str
        The files to be read into the data structure. Can be one file or co-temporal files of different wavelengths.
    align : bool, optional
        Whether or not to align two images of different wavelengths as there are slight discrepancies in positional information. This results in a slight crop of the images. Default is False.
    '''

    def __init__(self, files, align=False):
        self.mm_sun = 1391 << u.megameter
        self.ang_sun = 1920 << u.arcsec
        if type(files) == str:
            if ".fits" in files:
                if "ca" in files:
                    self.ca = fits.open(files)[0]
                    try:
                        self.ca_wvls = self.ca.header["spect_pos"] << u.Angstrom
                    except KeyError:
                        self.ca_wvls = fits.open(files)[1].data << u.Angstrom
                    self.px_res = self.ca.header["CDELT1"] << u.arcsec / u.pixel
                    self.pointing = (self.ca.header["CRVAL2"], self.ca.header["CRVAL1"]) << u.arcsec
                    self.mid = (self.ca.header["NAXIS2"] // 2, self.ca.header["NAXIS1"] // 2) << u.pixel
                else:
                    self.ha = fits.open(files)[0]
                    try:
                        self.ha_wvls = self.ha.header["spect_pos"] << u.Angstrom
                    except KeyError:
                        self.ha_wvls = fits.open(files)[1].data << u.Angstrom
                    self.px_res = self.ha.header["CDELT1"] << u.arcsec / u.pixel
                    self.pointing = (self.ha.header["CRVAL2"], self.ha.header["CRVAL1"]) << u.arcsec
                    self.mid = (self.ha.header["NAXIS2"] // 2, self.ha.header["NAXIS1"] // 2) << u.pixel
            elif ".h5" or ".hdf5" in files:
                if "ca" in files:
                    ca = h5py.File(files, "r")
                    self.ca = ObjDict({})
                    self.ca["data"] = ca["data"]
                    self.ca["header"] = yaml.load(ca["header"][0], Loader=yaml.Loader)
                    self.ca_wvls = self.ca.header["spect_pos"] << u.Angstrom
                    self.px_res = self.ca.header["pixel_scale"] << u.arcsec / u.pixel
                    self.pointing = (self.ca.header["crval"][-2], self.ca.header["crval"][-1]) << u.arcsec
                    self.mid = (self.ca.header["dimensions"][-2] // 2, self.ca.header["dimensions"][-1] // 2) << u.pixel
                else:
                    ha = h5py.File(files, "r")
                    self.ha = ObjDict({})
                    self.ha["data"] = ha["data"]
                    self.ha["header"] = yaml.load(ha["header"][0], Loader=yaml.Loader)
                    self.ha_wvls = self.ha.header["spect_pos"] << u.Angstrom
                    self.px_res = self.ha.header["pixel_scale"] << u.arcsec / u.pixel
                    self.pointing = (self.ha.header["crval"][-2], self.ha.header["crval"][-1]) << u.arcsec
                    self.mid = (self.ha.header["dimensions"][-2] // 2, self.ha.header["dimensions"][-1]) << u.pixel
        else:
            for f in files:
                if ".fits" in f:
                    if "ca" in f:
                        self.ca = fits.open(f)[0]
                        try:
                            self.ca_wvls = self.ca.header["spect_pos"] << u.Angstrom
                        except KeyError:
                            self.ca_wvls = fits.open(f)[1].data << u.Angstrom
                        self.px_res = self.ca.header["CDELT1"] << u.arcsec / u.pixel
                        self.pointing = (self.ca.header["CRVAL2"], self.ca.header["CRVAL1"]) << u.arcsec
                        self.mid = (self.ca.header["NAXIS2"] // 2, self.ca.header["NAXIS1"] // 2) << u.pixel
                    else:
                        self.ha = fits.open(f)[0]
                        try:
                            self.ha_wvls = self.ha.header["spect_pos"] << u.Angstrom
                        except KeyError:
                            self.ha_wvls = fits.open(f)[1].data << u.Angstrom
                elif ".h5" or ".hdf5" in f:
                    if "ca" in f:
                        ca = h5py.File(f, "r")
                        self.ca = ObjDict({})
                        self.ca["data"] = ca["data"]
                        self.ca["header"] = yaml.load(ca["header"][0], Loader=yaml.Loader)
                        self.ca_wvls = self.ca.header["spect_pos"] << u.Angstrom
                        self.px_res = self.ca.header["pixel_scale"] << u.arcsec / u.pixel
                        self.pointing = (self.ca.header["crval"][-2], self.ca.header["crval"][-1]) << u.arcsec
                        self.mid = (self.ca.header["dimensions"][-2] // 2, self.ca.header["dimensions"][-1] // 2) << u.pixel
                    else:
                        ha = h5py.File(f, "r")
                        self.ha = ObjDict({})
                        self.ha["data"] = ha["data"]
                        self.ha["header"] = yaml.load(ha["header"][0], Loader=yaml.Loader)
                        self.ha_wvls = self.ha.header["spect_pos"] << u.Angstrom

    def __str__(self):
        if "ca" and "ha" in self.__dict__:
            try:
                date = self.ca.header["DATE-AVG"][:10]
                time = self.ca.header["DATE-AVG"][11:-4]
                el_1 = self.ca.header["WDESC1"]
                samp_wvl_1 = str(self.ca.header["NAXIS3"])
                el_2 = self.ha.header["WDESC1"]
                samp_wvl_2 = str(self.ha.header["NAXIS3"])
                pointing = (str(round(self.ca.header["CRVAL1"],3)), str(round(self.ca.header["CRVAL2"],3)))
            except KeyError: # must be using hdf5 data files
                date = self.ca.header["date-obs"]
                time = self.ca.header["time-obs"]
                el_1 = self.ca.header["element"]
                samp_wvl_1 = str(self.ca.header["dimensions"][-3])
                el_2 = self.ha.header["element"]
                samp_wvl_2 = str(self.ha.header["dimensions"][-3])
                pointing = (str(self.ca.header["crval"][-1]), str(self.ca.header["crval"][-2]))
            if len(self.ca.data.shape) == 3:
                return f"CRISP observation from {date} {time} UTC with measurements taken in the elements {el_1} angstroms and {el_2} angstroms with {samp_wvl_1} and {samp_wvl_2} wavelengths sampled, respectively. Heliocentric coodinates at the centre of the image ({pointing[0]},{pointing[1]}) in arcseconds. Only Stokes I present in these observations."
            elif len(self.ca.data.shape) == 4:
               return f"CRISP observation from {date} {time} UTC with measurements taken in the elements {el_1} angstroms and {el_2} angstroms with {samp_wvl_1} and {samp_wvl_2} wavelengths sampled, respectively. Heliocentric coodinates at the centre of the image ({pointing[0]},{pointing[1]}) in arcseconds. All Stokes parameters present in these observations."
        elif "ca" and not "ha" in self.__dict__:
            try:
                date = self.ca.header["DATE-AVG"][:10]
                time = self.ca.header["DATE-AVG"][11:-4]
                el_1 = self.ca.header["WDESC1"]
                samp_wvl_1 = str(self.ca.header["NAXIS3"])
                pointing = (str(round(self.ca.header["CRVAL1"],3)), str(round(self.ca.header["CRVAL2"],3)))
            except KeyError:
                date = self.ca.header["date-obs"]
                time = self.ca.header["time-obs"]
                el_1 = self.ca.header["element"]
                samp_wvl_1 = str(self.ca.header["dimensions"][-3])
                pointing = (str(self.ca.header["crval"][-1]), str(self.ca.header["crval"][-2]))
            if len(self.ca.data.shape) == 3:
                return f"CRISP observation from {date} {time} UTC with measurements taken in the elements {el_1} angstroms with {samp_wvl_1} wavelengths sampled and with heliocentric coordinates at the centre of the image ({pointing[0]},{pointing[1]}) in arcseconds. Only Stokes I present in this observation."
            elif len(self.ca.data.shape) == 4:
                return f"CRISP observation from {date} {time} UTC with measurements taken in the elements {el_1} angstroms with {samp_wvl_1} wavelengths sampled and with heliocentric coordinates at the centre of the image ({pointing[0]},{pointing[1]}) in arcseconds. All Stokes parameters present in these observations."
        elif not "ca" and "ha" in self.__dict__:
            try:
                date = self.ha.header["DATE-AVG"][:10]
                time = self.ha.header["DATE-AVG"][11:-4]
                el_1 = self.ha.header["WDESC1"]
                samp_wvl_1 = str(self.ha.header["NAXIS3"])
                pointing = (str(round(self.ha.header["CRVAL1"],3)), str(round(self.ha.header["CRVAL2"],3)))
            except KeyError:
                date = self.ha.header["date-obs"]
                time = self.ha.header["time-obs"]
                el_1 = self.ha.header["element"]
                samp_wvl_1 = str(self.ha.header["dimensions"][-3])
                pointing = (str(self.ha.header["crval"][-1]), str(self.ha.header["crval"][-2]))
            if len(self.ha.data.shape) == 3:
                return f"CRISP observation from {date} {time} UTC with measurements taken in the element {el_1} angstroms with {samp_wvl_1} wavelengths sampled and with heliocentric coordinates at the centre of the image ({pointing[0]},{pointing[1]}) in arcseconds. Only Stokes I present in this observation."
            elif len(self.ha.data.shape) == 4:
                return f"CRISP observation from {date} {time} UTC with measurements taken in the element {el_1} angstroms with {samp_wvl_1} wavelengths sampled and with heliocentric coordinates at the centre of the image ({pointing[0]},{pointing[1]}) in arcseconds. All Stokes parameters present in these observations."

    def unit_conversion(self, coord, unit_to, centre=False):
        '''
        A method to convert unit coordinates between pixel number, arcsecond (either absolute or relative to pointing) and megametre.

        Parameters
        ----------
        coord : astropy.units.quantity.Quantity
            The coordinate to be transformed.
        unit_to : str
            The coordinate system to convert to.
        centre : bool, optional
            Whether or not to calculate the pixel in arcseconds with respect to the pointing e.g. in the helioprojective frame.
        '''

        if not centre:
            if unit_to == "pix":
                if coord.unit == "pix":
                    return coord
                elif coord.unit == "arcsec":
                    return np.round(coord / self.px_res)
                elif coord.unit == "megameter":
                    return np.round((coord * self.ang_sun / self.mm_sun) / self.px_res) 
            elif unit_to == "arcsec":
                if coord.unit == "pix":
                    return coord * self.px_res
                elif coord.unit == "arcsec":
                    return coord
                elif coord.unit == "megameter":
                    return coord * (self.ang_sun / self.mm_sun)
            elif unit_to == "Mm":
                if coord.unit == "pix":
                    return (coord * self.px_res) * self.mm_sun / self.ang_sun
                elif coord.unit == "arcsec":
                    return coord * self.mm_sun / self.ang_sun
                elif coord.unit == "megameter":
                    return coord
        else:
            # N.B. the conversions which take into account the centre pixel in the helioprojective coordinate frame assume that the given coordinate is in (y, x) format, whereas the other conversions can be done either way round e.g. (y, x) or (x, y)
            if unit_to == "pix":
                if coord.unit == "pix":
                    return coord
                elif coord.unit == "arcsec":
                    px_diff = np.round((coord - self.pointing) / self.px_res)
                    return self.mid + px_diff
                elif coord.unit == "megameter":
                    return self.unit_conversion(coord, unit_to="pix", centre=False)
            elif unit_to == "arcsec":
                if coord.unit == "pix":
                    return ((coord - self.mid) * self.px_res) + self.pointing
                elif coord.unit == "arcsec":
                    # N.B. the assumption here is that you will only use this if you want to convert from arcseconds to helioprojective coordinate frame
                    return (coord - (self.mid * self.px_res) + self.pointing)
                elif coord.unit == "megameter":
                    # this code is really fucking bad but I couldn't be bothered doing it properly so
                    return self.unit_conversion(self.unit_conversion(coord, unit_to="pix", centre=False), unit_to="arcsec", centre=True)
            elif unit_to == "megameter":
                if coord.unit == "pix":
                    return self.unit_conversion(coords, unit_to="pix", centre=False)
                elif coord.unit == "arcsec":
                    # ditto for this one
                    return self.unit_conversion(self.unit_conversion(coord, unit_to="pix", centre=True), unit_to="megameter", centre=False)
                elif coord.unit == "megameter":
                    return coord

    def intensity_vector(self, coord, line, pol=False, centre=False):
        '''
        A class method for returning the intensity vector of a given pixel.

        Parameters
        ----------
        coord : astropy.unit.quantity.Quantity
            The coordinate to give the intensity vector for.
        line : str
            The line to get the intensity vector for. Can be "ca" or "ha".
        pol : bool, optional
            Whether or not to return the polarimetric intensity vector. Default is False.
        centre : bool, optional
            Whether or not to calculate the pixel in arcseconds with respect to the pointing e.g. in the helioprojective frame.
        '''

        if line == "ha" and pol:
            raise WiseGuyError("Tryin' to be a wise guy, eh?")

        coord = self.unit_conversion(coord, unit_to="pix", centre=centre)

        if line.lower() == "ca":
            if not pol:
                if len(self.ca.data.shape) == 4:
                    return self.ca.data[0, :, *coord]
                else:
                    return self.ca.data[:, *coord]
            else:
                if len(self.ca.data.shape) == 4:
                    return self.ca.data[:, :, *coord]
                else:
                    raise WiseGuyError("Tryin' to be a wise guy, eh?")
        elif line.lower() == "ha":
            return self.ha.data[:, *coord]