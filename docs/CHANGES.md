# Changelog

## Version 1.0.1 (unreleased)

- Add CNIC (Computerized National Identity Card) to Patients and Samples,
  handled like senaite.patient handles the Medical Record Number but as a
  separate, optional identifier: patient lookup in the sample add form,
  unique per patient, indexed, searchable, listed, field permissions per
  workflow state
- Add patient email and phone to Samples, autocomplete all patient fields
  (including middle name) when a patient is picked by MRN or CNIC, and copy
  the patient data of samples to existing patients
- Use the Sample Point as mandatory "District of Residence" of samples
- Reduce the address of patients to the physical address
- #6 Stop asking Zope to install senaite.jsonapi as a product
- #5 Ignore the scripts a buildout run generates
- #4 Declare the translation domain in the package's ZCML
- #3 Pin the SENAITE packages to 2.6.0
- #2 Name the development configuration the way the file is named
- #1 Register the sample type behavior so the extended field is applied

## Version 1.0.0 - (2024-12-20)

- Add-on created
