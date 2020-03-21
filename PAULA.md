# PAULA

Conversion of STREUSLE into the PAULA format is possible using [Pepper](https://corpus-tools.org/pepper/) and the [STREUSLE Pepper Importer](https://github.com/nert-nlp/pepper-streusle-importer).

## Pepper Setup

Download [the latest stable release of Pepper](https://korpling.german.hu-berlin.de/saltnpepper/pepper/download/stable/) and unzip it:

```
wget https://korpling.german.hu-berlin.de/saltnpepper/pepper/download/stable/Pepper_2019.06.11.zip
cd pepper
```

## Importer Module Compilation
Clone the repository and compile the JAR. (You will need `mvn` installed.)

```
git clone https://github.com/nert-nlp/pepper-streusle-importer.git
cd pepper-streusle-importer
mvn package
```

Place the JAR in Pepper's `plugins` folder:

```
cp target/streusle-1.0.0-SNAPSHOT.jar ../plugins/
cd .. # return to root pepper dir
```

## Pepper configuration setup

Make a directory that will hold all STREUSLE-related data and initialize a Pepper config for it:

```
mkdir streusle
touch streusle/streusle.pepper
```

Using your favorite editor, initialize the Pepper config at `streusle/streusle.pepper`:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<pepper-job id="streusle" version="1.0">
  <importer name="StreusleImporter" path="./streusle/">
  </importer>
  <exporter name="PAULAExporter" path="./out/paula/">
  </exporter>
</pepper-job>
```

## STREUSLE data prep
Prepare the enriched STREUSLE JSON and split it by document:

```bash
git clone https://github.com/nert-nlp/streusle.git streusle_repo
cd streusle_repo
python conllulex2json.py streusle.conllulex > streusle.json
python govobj.py streusle.json > streusle.gov.json
python split_streusle_json.py streusle.gov.json ../streusle/streusle
cd ..
```

## Run Pepper Job

```
bash pepperStart.sh -p streusle/streusle.pepper
```

The data will be available at `streusle/out/paula` on completion
