

import api as api

v = {'subjects':['subject1','subject2','subject3']}

dset = 'template'

p = api.Pipe(v)

b = api.BlurFunctional()

b.dset = dset

atonii = api.ConvertToNifti()

#atonii.dset = dset

corm = api.CorrectMotion()

#corm.dset = dset
corm.motionlabel = 'motionlabel.1D'

hipas = api.HighpassFilter()
#hipas.dset = dset

norm = api.NormalizeFunctional()
#norm.dset = dset

ranat = api.ReconstructAnatomicalCNI()
ranat.anat_name = 'anat'
ranat.raw_anat = '001_T1.nii.gz'

rfunc = api.ReconstructFunctionalCNI()
#rfunc.dset = dset
rfunc.raw_funcs = ['raw1.nii','raw2.nii']
rfunc.leadin = 4
rfunc.leadout = 6

warpanat = api.WarpAnatomical()
warpanat.anat_name = 'anat'
warpanat.talairach_path = '../scripts'

warpfunc = api.WarpFunctional()
warpfunc.anat_name = 'anat'
#warpfunc.dset = dset
warpfunc.talairach_dxyz = 2.9



p.add(b,atonii,corm,hipas,norm,ranat,rfunc,warpanat,warpfunc)

p.writeout()







