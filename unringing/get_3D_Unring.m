function NewImg = get_3D_Unring(Img)
s=size(Img);

for i=1:s(1)
    Slice(:,:)=Img(i,:,:);
    NewSlice=unring(Slice);
    NewImg(i,:,:)=NewSlice(:,:);
end

for i=1:s(2)
   Slice2(:,:)=NewImg(:,i,:);
   NewSlice2=unring(Slice2);
   NewImg2(:,i,:)=NewSlice2(:,:);
end

NewImg=NewImg2;

end