while read p; do
  echo $p
  cd $p
  zip -r $p.zip .
  cd ../
done <dirs.txt
