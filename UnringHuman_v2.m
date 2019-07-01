root_path='/home/liamlinux/Documents/Current Analysis_v2';
subfolders={'Precon','Postcon','Blood','PreconKidney','PostconKidney'};
ss=size(subfolders);

Folders=dir(root_path);
sss=size(Folders);
n=0;
for i=1:sss(1)
    if Folders(i).isdir && ~(strcmp(Folders(i).name, '.') ||  strcmp(Folders(i).name, '..'))
        n=n+1;
        PatientFolders{n,1}=Folders(i).name;
    end
end
sss=size(PatientFolders);

Working_Folder='Nii_working';
for i=5:1:sss(1)
    PathName=strcat(root_path,'/', PatientFolders{i,1});
    for j=1:ss(2)
        session=subfolders{j};
        subpath1=strcat(PathName, '/', Working_Folder, '/', session);
        Nii_folder=strcat(subpath1,'NIFTI_Renamed');
        if exist(Nii_folder)==7
            Files=dir(Nii_folder);
            s=size(Files);
            for k=1:s(1)
                if contains(Files(k).name,'UTE')
                %if  ~(strcmp(Files(k).name, '.') ||  strcmp(Files(k).name, '..') || contains(Files(k).name, 'fMRI') || contains(Files(k).name, 'trufi') || contains(Files(k).name, '_uro_') || contains(Files(k).name, 'FLAIR') || contains(Files(k).name, 'swi'))
                    loadname=strcat(Files(k).folder, '/', Files(k).name);
                    loadname
                    Nii=load_nii(loadname);
                    Img=double(Nii.img);
                    NewImg = get_3D_Unring(Img);
                    NewNii=Nii;
                    NewNii.img=NewImg;
                    cd(Files(k).folder)
                    savename=strcat('unring_', Files(k).name);
                    save_nii(NewNii, savename);
                end
            end
        end
    end
    i
end
