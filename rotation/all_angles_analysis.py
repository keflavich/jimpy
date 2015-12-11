#!/usr/bin/python2.7

import os
import sys

import numpy
from numpy import *

from scipy.stats import ks_2samp


import healpy
import string

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
from pylab import *
from matplotlib import colors
from matplotlib import rc
rc('font',**{'family':'serif','serif':['Times New Roman'],'size':12})
rc('text',usetex=True)
rc('patch',antialiased=False)



import moment_maps_rotate

#look for files to process

diri='./'

try:
   finfo=sys.argv[1]
except:
   print 'Need filename or filename root'
   raise IndexError

file_list=[os.path.expanduser(sys.argv[1])]


nfiles=len(file_list)

if nfiles < 1:
   print 'No files found to process'
   raise IndexError
else:
   print 'Processing ',nfiles,' files'

#variables for screenshots - NB imcol expects units in CODE UNITS

subplots_adjust(hspace=0.1)
subplots_adjust(wspace=0.1)

# conversion factor gcm^-2 --> Av
extfactor=1./1.67e-24/1.e21

# physical limits on field-of-view

xmin=-20.
xmax=20.
ymin=-20.
ymax=20.
zmin=-100.
zmax=100.

# pixel dimensions of images

iline=100

# dimensions of plot array

nplotx=6
nploty=4

# size of multi-plots

fsize=(18,27)

# column-density colorbar limits

logsigmax=0.3
logrange=4
logsigmin=logsigmax-logrange

# velocity colorbar limits

vmax=5.
vmin=-5.

# limits for mean pdf:
limitsmean=[0.,2,-2.,6.]

# lower limit for cdf column densities
#cmflowlimit=limitsmean[0]
cmflowlimit=0.
# set negative for no cmfhighlimit
cmfhighlimit=-1.


normsig=colors.Normalize(vmin=logsigmin,vmax=logsigmax)
normvel=colors.Normalize(vmin=vmin,vmax=vmax)
normsigav=colors.Normalize(vmin=log10((10.**logsigmin)*extfactor),vmax=log10((10.**logsigmax)*extfactor))

# temperature thresholds (gas below coldtemp and above hottemp is rejected)

coldtemp=0.
hottemp=125.



# masks for non-antiparallel Healpix vectors

level0mask=[0,1,2,3,4,5]
level1mask=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]

# set Healpix level

nhplevel=1
nhppix=12*4**nhplevel

if nhplevel==0:
    mask=level0mask
elif nhplevel==1:
    mask=level1mask
else:
    print 'This script is too dumb to handle Healpix level',nhplevel
    raise IndexError

print 'Healpix level: ',nhplevel
print 'Healpix wedges: ',nhppix

healpix_angles = zip(*healpy.pix2ang(nhplevel+1, np.arange(nhppix)))

rad_to_deg=360./(2.*pi)

xlab='x(pc)'
ylab='y(pc)'

#plt.tight_layout()

shr=0.73

extent=(xmin,xmax,ymin,ymax)

fname=file_list[0]

moment0maps=[]
moment1maps=[]
pdfs=[]

for ihppix in range(nhppix):
  if (ihppix) in mask:
   print 'Plotting: ',ihppix,' of ',nhppix,' images, nplotx,y=',nplotx,nploty

   angles=healpix_angles[ihppix]

   angle1=angles[1]*rad_to_deg
   angle2=0.0
   angle3=angles[0]*rad_to_deg


   print 'Angles: ',angle1,angle2,angle3

#call wrapper for imcol

   fnamei=fname

   maps=moment_maps_rotate.imager(fnamei,xmin,xmax,ymin,ymax,zmin,zmax,logsigmax,logrange,logsigmin,angle1,angle2,angle3,iline,coldtemp,hottemp)

   moment0=maps[0]
   moment1=maps[1]
   
   

   moment0maps.append(moment0)
   moment1maps.append(moment1)


nmaps=len(moment0maps)

##########################################################################################
#
#   ZEROTH MOMENT MAPS
#
##########################################################################################

fig=plt.figure(figsize=fsize)

set_cmap('hot')

nplot=0

for i in range(nmaps):
        nplot+=1
        plt.subplot(nplotx,nploty,nplot)

        moment0=moment0maps[nplot-1]

        imgplot=plt.imshow(moment0+np.log10(extfactor),extent=extent,origin='lower',interpolation='nearest')
#       imgplot.set_norm(normsig)
        imgplot.set_norm(normsigav)
                
        plt.contour(moment0*extfactor,levels=[10.**0.5,10.**1.],colors='white')
        
        plt.title('Wedge '+str(i))
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        xlabel(xlab)
        ylabel(ylab)

cax = plt.axes([0.95, 0.1, 0.03, 0.8])


cb=plt.colorbar(imgplot, cax=cax)
cb.set_label('Log(column density) (g cm$^{-2}$)')

plt.savefig('moment0_angles_'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

clf()
cla()

##########################################################################################
#
#   FIRST MOMENT MAPS
#
##########################################################################################

fig=plt.figure(figsize=fsize)

set_cmap('rainbow')

nplot=0

for i in range(nmaps):
        nplot+=1
        plt.subplot(nplotx,nploty,nplot)

        moment1=moment1maps[nplot-1]

        imgplot=plt.imshow(moment1,extent=extent,origin='lower',interpolation='nearest')
        imgplot.set_norm(normvel)

        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        xlabel(xlab)
        ylabel(ylab)

cax = plt.axes([0.95, 0.1, 0.03, 0.8])

cb=plt.colorbar(imgplot, cax=cax)
cb.set_label('Line-of-sight velocity (km s$^{-1}$)')
plt.savefig('moment1_angles_'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

clf()
cla()

##########################################################################################
#
#   MEAN PDF
#
##########################################################################################

fig=plt.figure(figsize=(8,8))

for i in range(nmaps):
        pdf=ravel(moment0maps[i])
        pdf=[log10((10.**p)*extfactor) for p in pdf]
        pdfs.append(pdf)
#       print pdf

meanpdf=[]
stdpdf=[]
actualns=[]
cmfxs=[]
cmfys=[]
nbins=50
for coldenslist in pdfs:
        n,bins,patches=plt.hist(coldenslist,bins=nbins,range=(-3,3),log=True,histtype='step',fill=False)
        actualns.append(n)
# crop cdf at lower surf dense limit
        cmf=sort(coldenslist)
        nlist=len(coldenslist)
        for i in range(nlist):
                if cmf[i]>cmflowlimit:
                        cmftrim=cmf[i:]
                        ncmf=len(cmftrim)
                        break

                
        if cmfhighlimit<0.:
                ncmf=len(cmftrim)
                fncmf=float(ncmf)
                cmfxs.append(cmftrim)
                cmfys.append((arange(ncmf))/fncmf)
        else:
                for j in range(ncmf):
                        cmftrim=cmftrim[:j]
#                       print i,j
                        ncmf=len(cmftrim)
                        fncmf=float(ncmf)
                        cmfxs.append(cmftrim)
                        cmfys.append((arange(ncmf))/fncmf)
                        break

# perform KS tests of all against all

clf()
cla()
fig=plt.figure(figsize=(8,8))

for i in range(nmaps):
        for j in range(nmaps):
                if i!=j:
                        ks=ks_2samp(cmfxs[i], cmfxs[j])
                        plt.plot(float(i+1),ks[0],'bx')
                        print i,j,ks
   
xlabel('Healpix wedge')
ylabel('KS statistics')

plt.savefig('ks_stats_'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

clf()
cla()
fig=plt.figure(figsize=(8,8))

for i in range(nmaps):
        for j in range(nmaps):
                if i!=j:
                        ks=ks_2samp(cmfxs[i], cmfxs[j])
                        plt.plot(float(i+1),ks[1],'bx')
   
xlabel('Healpix wedge')
ylabel('KS p-value')

plt.savefig('ks_p-values_'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

clf()
cla()
fig=plt.figure(figsize=(8,8))

grid=zeros((nmaps,nmaps))
for i in range(nmaps):
        for j in range(nmaps):
                if i<=j:
                        ks=ks_2samp(cmfxs[i], cmfxs[j])
                        grid[i,j]=ks[1]
   
plt.imshow(grid,cmap='hot',interpolation='nearest',origin='lower')
xlabel('Healpix wedge')
ylabel('Healpix wedge')
colorbar()

plt.savefig('ks_grid_'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

clf()
cla()

for j in range(nbins):
    binvalues=[]
    for i in range(nmaps):
        binvalues.append((actualns[i][j]))
    av=mean(binvalues)
    st=std(binvalues)
    if av<1e-2:av=1e-2
    meanpdf.append(av)
    stdpdf.append(st)

high=[]
low=[]
for i in range(nbins):
    hi=meanpdf[i]+stdpdf[i]
    if hi<0:hi=1e-2
    high.append(hi)
    lo=meanpdf[i]-stdpdf[i]
    if lo<0:lo=1e-2
    low.append(lo)

bns=[]
for i in range(nbins):
        bns.append(0.5*(bins[i]+bins[i+1]))
        
sh=sum(high)
sm=sum(meanpdf)
sl=sum(low)

high=[log10(h) for h in high]
meanpdf=[log10(m) for m in meanpdf]
low=[log10(l) for l in low]


#plt.plot(bins,high,'r--')
plt.plot(bns,meanpdf,'b-')
#plt.plot(bins,meanpdfi,'r-')
#plt.plot(bins,low,'r--')
plt.fill_between(bns, low, high, edgecolor=None,facecolor='blue',alpha=0.5,interpolate=True)
#plt.fill_between(bins, lowi, highi, edgecolor=None,facecolor='red',alpha=0.5,interpolate=True)
xlab='log A$_{\\rm V}$'
ylab='log P(A$_{\\rm V}$)'
xlabel(xlab)
ylabel(ylab)
axis(limitsmean)
plt.savefig('moment0_meanpdf'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

##########################################################################################
#
#   INDIVIDUAL CMFS
#
##########################################################################################

fig=plt.figure(figsize=fsize)

nplot=0
for i in range(nmaps):
#       nplot+=1
#        plt.subplot(nplotx,nploty,nplot)
        plt.plot(cmfxs[i],cmfys[i])
        xlab='log A$_{\\rm V}$'
        ylab='log P(A$_{\\rm V}$)'
        xlabel(xlab)
        ylabel(ylab)
#       axis(limitsmean)

plt.savefig('cmfs_angles'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

##########################################################################################
#
#   INDIVIDUAL PDFS COMPARED TO MEAN
#
##########################################################################################

fig=plt.figure(figsize=fsize)

nplot=0
for i in range(nmaps):
        nplot+=1
        plt.subplot(nplotx,nploty,nplot)
        plt.plot(bns,meanpdf,'b-')
        pdfi=actualns[i]
        pdfi=[log10(p) for p in pdfi]
        plt.plot(bns,pdfi,'k-')
        xlab='log A$_{\\rm V}$'
        ylab='log P(A$_{\\rm V}$)'
        xlabel(xlab)
        ylabel(ylab)
        axis(limitsmean)

plt.savefig('pdfs_angles'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')


fig=plt.figure(figsize=fsize)

nplot=0
for i in range(nmaps):
        plt.plot(bns,meanpdf,'-')
        pdfi=actualns[i]
        pdfi=[log10(p) for p in pdfi]
        plt.plot(bns,pdfi,'k-')
        xlab='log A$_{\\rm V}$'
        ylab='log P(A$_{\\rm V}$)'
        xlabel(xlab)
        ylabel(ylab)
        axis(limitsmean)

plt.savefig('all_pdfs_angles'+os.path.split(fname)[-1]+'.png',dpi=300,bbox_inches='tight')

# https://github.com/keflavich/plfit
import plfit

ks_pl = []
ks_ln = []
ks_pl_nofit = []
ks_ln_nofit = []

for row in cmfxs:
    pf = plfit.plfit(10**np.array(row))
    pf.lognormal()
    ks_pl.append(pf._ks_prob)
    ks_ln.append(pf.lognormal_ksP)

    pf = plfit.plfit(10**np.array(row), xmin=10**0.5)
    pf.lognormal()
    ks_pl_nofit.append(pf._ks_prob)
    ks_ln_nofit.append(pf.lognormal_ksP)

plt.clf()
plt.plot(ks_pl, ks_ln, 'bo')
plt.plot(ks_pl_nofit, ks_ln_nofit, 'ro')

# plot cutoffs
plt.plot([0.05,0.05],[0,1],'k--')
plt.plot([0,1],[0.05,0.05],'k--')    
plt.xlabel("Powerlaw KS Probability")
plt.ylabel("Lognormal KS Probability")


print 'Done!'
