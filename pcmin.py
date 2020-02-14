"""
:module: pcmin


"""

import logging

import numpy as np

EPS = 0.622
gPressureUnits = "hPa"

def satVapPr(temp, units_vp=gPressureUnits):
    """
    Saturation vapour pressure from temperature in degrees celsius.

    :param float temp: Temperature (degrees celsius).
    :param str units_vp: Units of the vapour pressure to return.
                         Default is ``gPressureUnits``.

    :returns: saturation vapour pressure in the specified or default units.

    .. note::
       Calculation is in kPa with a conversion at the end to the
       required units.


    Example::

        >>> from metutils import satVapPr
        >>> satVapPr(25.)
        31.697124349060619

    """
    vp = np.exp(((16.78 * temp) - 116.9) / (temp + 237.3))
    vp = vp / 10.

    return vp


def vapPrToMixRat(es, prs):
    """
    Calculate mixing ratio from vapour pressure
    In this function, we (mis)use the symbol es for vapour pressure,
    when it correctly represents saturation vapour pressure.
    The function can be used for both.

    :param float es: Vapour pressure.
    :param float prs: Air pressure (hPa).

    :returns: Mixing ratio.
    :rtype: float

    """
    rat = EPS * es / (prs - es)
    return rat

def mixRatToVapPr(rat, prs):
    """
    Calculate vapour pressure from mixing ratio.

    :param float rat: Mixing ratio (g/kg).
    :param float prs: Air pressure (hPa).

    :returns: Vapour pressure.
    :rtype: float
    """
    es = rat * prs / (EPS + rat)
    return es

def pcmin(sst, psl, p, t, r):
    """
    Calculate maximum wind speed and minimum central pressure 
    achievable in tropical cyclones, given a vertical profile and 
    sea surface temperature. 

    This is a Python implementation of Kerry Emanuel's pcmin routine:

    :param float sst: Sea surface temperature (C)
    :param float psl: sea level pressure (hPa)
    :param p: :class:`numpy.ndarray` pressure values (hPa)
    :param t: :class:`numpy.ndarray`  of temperature profile (K)
    :param r: :class:`numpy.ndarray` of mixing ratio profile (g/kg)


    """

    # Ratio of C_k to C_D
    ckcd = 0.9
    sigma = 0.0
    idiss = True

    # Exponent in assumed profile of azimuthal velocity inside the eye
    # V = V_m(r/r_m)^b
    # NOTE: Kepert assumes a cubic prifile in the eye to avoid a 
    # barotropic instability (see Kepert & Wang (J. Atmos. Sci., 2001)) 
    b = 2.0

    # Set level from which parel is lifted
    nk = 1

    # Surface wind reduction factor:
    vreduc = 0.8

    sst += 273.15 # Convert to Kelvin
    r *= 0.001 # convert from g/kg to kg/kg
    t += 273.15 # Convert to Kelvin
    # Default values:
    T0 = 230.0
    vmax = 0.0
    pmin = 0.0
    ifl = False

    try:
        assert(sst > 5)
    except AssertionError:
        raise ValueError(f"SST is too low: {sst}")
    
    es0 = satVapPr(sst)

    try:
        assert(t.min() > 0)
    except AssertionError:
        raise ValueError("Temperature data invalid")

    iflag = True
    nint = 0
    pm = 970.0
    pmold = pm
    pnew = 0.0

    tp = t[nk]
    rp = r[nk]
    pp = p[nk]
    (capea, toa, iflag) = cape(tp, rp, pp, t, r, p, sigma)

    while np.abs(pnew - pmold) > 0.2:
        tp = t[nk]
        pp = min(pm, 1000.)
        rp = 0.22 * r[nk] * psl / (pp * (0.622 + r[nk]) - r[nk] * psl)
        (capem, tom, iflag) = cape(tp, rp, pp, t, r, p, sigma)
        if iflag: ifl = False
        tp = sst
        pp = min(pm, 1000.)
        rp = 0.622 * es0 / (pp - es0)
        capems, toms, iflag = cape(tp, rp, pp, t, r, p, sigma)
        T0 = toms
        if iflag: ifl = False
        if idiss: 
            rat = sst / toms
        else:
            rat = 1.

        rs0 = rp
        tv1 = t[0] * (1. + r[0]/0.622)/(1 + r[0])
        tvav = 0.5 * (tv1 + sst * (1. + rs0/0.622)/(1. + rs0))
        cat = capem - capea + 0.5 * ckcd * rat * (capems - capem)
        cat = max(cat, 0.0)
        pnew = psl * np.exp(-cat / (287.04 * tvav))
        pmold = pm
        pm = pnew
        nint += 1
        if (nint > 200) or (pm < 400):
            pmin = psl
            vmax = 0
            ifl = False
            return pmin, vmax, ifl
    
    catfac = 0.5 * (1. + 1. / b)
    cat = capem - capea + ckcd * rat * catfac * (capems - capem)
    cat = max(cat, 0.)
    pmin = psl * np.exp(-cat / (287.94 * tvav))
    fac = max(0.0, (capems - capem))
    vmax = vreduc * np.sqrt(ckcd * rat * fac)

    return pmin, vmax, True

def cape(tp, rp, pp, t, r, p, sigma):
    """

    :param float tp: Parcel temperature (K) 
    :param float rp: Parcel mixing ratio (g/g)
    :param float pp: Parcel pressure (hPa)
    :param t: :class:`numpy.ndarray` of temperature profile (K)
    :param r: :class:`numpy.ndarray` of mixing ratio profile (g/g)
    :param p: :class:`numpy.ndarray` of pressure profile (hPa)
    :param boolean sigma: Adjustable constant for buoyancy of displaced parcels
                          False=Reversible ascent
                          True=Pseudo-adiabatic ascent

    """

    ptop=59
    nold = len(p)
    n = 1
    for i in range(nold, 0, -1):
        if p[i] > ptop:
            n = max(n, i)
    if n < nold:
        p[n + 1:nold] = 0
        t[n + 1:nold] = 0
        r[n + 1:nold] = 0
    
    tvrdif = np.zeros(n)

    jmin = np.where(p < pp)[0].min()
    caped = 0.0
    tob = t[0]
    iflag = True

    if (rp < 1e-6) or (tp < 200):
        raise ValueError("Invalid surface variables - check surface temperature and mixing ratio data")

    cpd = 1005.7
    cpv = 1870.0
    cl = 2500.0
    cpvmcl = cpv - cl
    rv = 461.5
    rd = 287.04
    eps = rd / rv
    alv0 = 2.5e6

    # Define parcel quantities
    tpc = tp - 273.15
    esp = satVapPr(tpc)
    evp = rp * pp / (eps + rp)
    rh = min(evp / esp, 1.0)
    alv = alv0 + cpvmcl * tpc
    s = (cpd + rp * cl) * np.log(tp) - rd * np.log(pp - evp) + alv*rp/tp - rp*rv*np.log(rh)

    # Find LCL pressure
    chi = tp / (1669.0 - 1220 * rh - tp)
    plcl = pp * np.power(rh, chi)

    ncmax = 0

    for j in range(jmin, n):
        if p[j] >= plcl:
            # Parcel quantities below LCL
            tg = tp * (p[j]/pp)^(rd/cpd)
            rg = rp

            # calculate buoyancy:
            tlvr = tg * (1 + rg/eps) / (1 + rg)
            tvrdif[j] = tlvr - t[j] * (1 + r[j]/eps)/(1 + r[j])
        else:
            # Parcel quantities above LCL
            tgnew = t[j]
            tjc = t[j] - 273.15
            es = satVapPr(tjc)
            rg = vapPrToMixRat(es, p[j])

            # Iteratively calculate lifted parcel temperature and mixing ratio
            # For reversible ascent
            nc = 0
            tg = 0.0

            while (np.abs(tgnew - tg)) > 0.0:
                tg = tgnew
                tc = tg - 273.15
                enew = satVapPr(tc)
                rg = vapPrToMixRat(enew, p[j])

                nc += 1

                # Calculate estimates of rate of change of entropy with 
                # temperature at constant pressure

                alv = alv0 + cpvmcl * (tg - 273.15)
                sl = (cpd + rp * cl + alv * alv * rg/(rv * tg * tg)) / tg
                em = mixRatToVapPr(rg, p[j])
                sg = (cpd + rp * cl) * np.log(tg) - rd * np.log(p[j] - em) + alv * rg / tg
                if nc < 3:
                    ap = 0.3
                else:
                    ap = 1.0
                tgnew = tg + ap * (s - sg)/sl
                if (nc > 500) or (enew > (p[j] - 1)):
                    logging.debug("No convergence")
                    return caped, tob, False
                
            ncmax = max(nc, ncmax)

            # Calculate buoyancy:
            rmean = sigma * rg + (1 - sigma) * rp
            tlvr = tg * (1 + rg/eps)/(1 + rmean)
            tvrdif[j] = tlvr - t[j]*(1 + r[j]/eps)/(1 + r[j])
    
    # Positive and negative areas
    na = 0.
    pa = 0.
    
    inb = 1
    for j in range(n, jmin -1):
        if tvrdif[j] > 0:
            inb = max(inb, j)
    if inb == jmin:
        return caped, tob, False
    
    # Find positive and negative area and CAPE
    if inb > 1:
        for j in range(jmin + 1, inb):
            pfac = rd * (tvrdif[j] + tvrdif[j-1]) * (p[j-1] - p[j])/(p[j] + p[j-1])
            pa = pa + max(pfac, 0.0)
            na = na - min(pfac, 0.0)
        

        # Find area between parcel pressure and first level above it:
        pma = pp + p[jmin]
        pfac = rd * (pp - p[jmin])/pma
        pa = pa + pfac * max(tvrdif[jmin], 0.0)
        na = na - pfac * min(tvrdif[jmin], 0.0)

        # Residual positive area above inb and outflow temperature tob
        pat = 0.0
        tob = t[inb]

        if inb < n:
            pinb = (p[inb + 1]*tvrdif[inb] - p[inb] * tvrdif[inb+1]) / (tvrdif[inb] - tvrdif[inb + 1])
            pat = rd * tvrdif[inb] * (p[inb] - pinb) / (p[inb + pinb])
            tob = (t[inb] * (pinb - p[inb-1])) + t[inb+1] * (p[inb] - pinb) / (p[inb] - p[inb+1])
        
        # Calculate CAPE
        caped = pa + pat - na
        caped = max(caped, 0.0)

    return caped, tob, True
