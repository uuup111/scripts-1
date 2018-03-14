function runBTK(btkdir,Processeddir)

%btkdir="/home/js247994/DocumentsN2/Test2/fbrain-build";
btkfunc=strcat(btkdir,'/Applications/btkNLMDenoising');
%Processeddir='/neurospin/ciclops/projects/BIPLi7/ClinicalData/temp/';

S = dir(Processeddir);
S=S(~ismember({S.name},{'.','..'}));
%nbsubjects=sum([S.isdir]);

for subj=S'
    if subj.isdir==1
        subjpath=subj.name;
        TPIpathinput=strcat(Processeddir,'/',subjpath,'/TPI/Reconstruct_gridding/02-PostQuantif/');
        TPIpathoutput=strcat(Processeddir,'/',subjpath,'/TPI/Reconstruct_gridding/03-Filtered/');  
        if ~exist(TPIpathoutput,'dir')
            mkdir(TPIpathoutput)
        end        
        T= dir(TPIpathinput);
        T=T(~ismember({T.name},{'.','..'}));
        for file=T'
            filename=file.name;
            dotf=(strfind(filename,'.'));
            if strcmp(filename(dotf:dotf+3),'.nii')
                %newfilepath=strcat(filename(1:dotf-1),'_filtered.nii');
                filepath=strcat(TPIpathinput,'/',filename);
                newfilepath=strcat(TPIpathoutput,filename(1:dotf),'.nii');
                codelaunch=strcat(btkfunc,{' '},'-i',{' '},filepath,{' '},'-o',{' '},newfilepath);
                status = system(codelaunch{1});
            end
        end
    end
end
