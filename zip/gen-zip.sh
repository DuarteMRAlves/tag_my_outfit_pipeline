CURRENT_DIR=$(pwd)

WORKDIR=$(mktemp -d)

echo "Created temp directory '${WORKDIR}'"

cp -r Config Crop images docker-compose.yml ${WORKDIR}
cp zip/README.md ${WORKDIR}/README.md

echo "Copied zip files to temp directory"

cd ${WORKDIR}

echo "Changed directory to '${WORKDIR}'"

zip -r tag-my-outfit-pipeline.zip README.md Config Crop images docker-compose.yml

echo "Created zip file 'tag-my-outfit-pipeline.zip'"

cd "${CURRENT_DIR}"

echo "Changed directory to '${CURRENT_DIR}'"

mv ${WORKDIR}/tag-my-outfit-pipeline.zip .

rm -r "${WORKDIR}"

echo "Removed temp directory '${WORKDIR}'"