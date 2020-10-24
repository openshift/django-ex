import random
import re

from django.conf import settings

from edivorce.apps.core.models import Document, UserResponse
from edivorce.apps.core.utils.derived import get_derived_data


def file_documents(user, responses, initial=False):
    errors = []
    if not initial:
        user_has_submitted_initial = _get_response(user, 'initial_filing_submitted')
        if not user_has_submitted_initial:
            errors.append("You must file the initial filing first before submitting the final filing.")
        court_file_number = _get_response(user, 'court_file_number')
        if not court_file_number:
            errors.append("You must input your Court File Number")
    uploaded_forms, _ = forms_to_file(responses, initial)
    for form in uploaded_forms:
        docs = Document.objects.filter(bceid_user=user, doc_type=form['doc_type'], party_code=form.get('party_code', 0))
        if docs.count() == 0:
            errors.append(f"Missing documents for {Document.form_types[form['doc_type']]}")

    if errors:
        return errors

    # Save dummy data for now. Eventually replace with data from CSO
    prefix = 'initial' if initial else 'final'
    _save_response(user, f'{prefix}_filing_submitted', True)

    if not initial:
        _save_response(user, f'final_filing_status', 'Submitted')

    package_number_parts = []
    for _ in range(3):
        num = ''
        for _ in range(3):
            num += str(random.randint(0, 9))
        package_number_parts.append(num)

    package_number = '-'.join(package_number_parts)
    _save_response(user, f'{prefix}_filing_package_number', package_number)

    if settings.DEPLOYMENT_TYPE == 'localdev':
        base_url = 'https://dev.justice.gov.bc.ca'
    else:
        base_url = settings.PROXY_BASE_URL

    receipt_link = base_url + '/cso/payment/viewReceipt.do?packageNumber=' + package_number
    _save_response(user, f'{prefix}_filing_receipt_link', receipt_link)

    package_link = base_url + '/cso/register.do?packageNumber=' + package_number
    _save_response(user, f'{prefix}_filing_package_link', package_link)


def _save_response(user, question, value):
    response, _ = UserResponse.objects.get_or_create(bceid_user=user, question_id=question)
    response.value = value
    response.save()


def _get_response(user, question):
    response = UserResponse.objects.filter(bceid_user=user, question_id=question).first()
    if response:
        return response.value


def forms_to_file(responses_dict, initial=False):
    generated = []
    uploaded = []

    how_to_file = responses_dict.get('how_to_file')
    how_to_sign = responses_dict.get('how_to_sign')
    signing_location_both = responses_dict.get('signing_location') if how_to_sign == 'Together' else None
    signing_location_you = responses_dict.get('signing_location_you') if how_to_sign == 'Separately' else None
    signing_location_spouse = responses_dict.get('signing_location_spouse') if how_to_sign == 'Separately' else None

    derived = responses_dict.get('derived', get_derived_data(responses_dict))

    name_change_you = derived['wants_other_orders'] and responses_dict.get('name_change_you') == 'YES'
    name_change_spouse = derived['wants_other_orders'] and responses_dict.get('name_change_spouse') == 'YES'
    has_children = derived['has_children_of_marriage']

    provide_marriage_certificate = responses_dict.get('original_marriage_certificate') == 'YES'
    married_in_canada = responses_dict.get('where_were_you_married_country') == 'Canada'
    marriage_province = responses_dict.get('where_were_you_married_prov', '').strip().upper()
    married_in_quebec = married_in_canada and marriage_province.lower().startswith('q')

    if initial:
        generated.append({'doc_type': 'NJF', 'form_number': 1})
        if provide_marriage_certificate:
            uploaded.append({'doc_type': 'MC', 'party_code': 0})
            if married_in_quebec:
                uploaded.append({'doc_type': 'AFTL', 'party_code': 0})

        if signing_location_both == 'In-person' or signing_location_you == 'In-person':
            # claimant 1 is signing with a commissioner
            uploaded.append({'doc_type': 'RDP', 'party_code': 0})

        elif signing_location_you == 'Virtual' and signing_location_spouse == 'In-person':
            # claimant 1 is signing virtually and claimant 2 is not
            generated.append({'doc_type': 'RFO', 'form_number': 35})
            generated.append({'doc_type': 'RCP', 'form_number': 36})
            uploaded.append({'doc_type': 'OFI', 'party_code': 0})
            uploaded.append({'doc_type': 'EFSS', 'party_code': 1})
            uploaded.append({'doc_type': 'RDP', 'party_code': 0})
            if has_children:
                uploaded.append({'doc_type': 'AAI', 'party_code': 0})
            if name_change_you:
                uploaded.append({'doc_type': 'NCV', 'party_code': 1})

        elif signing_location_both == 'Virtual' or (signing_location_you == 'Virtual' and signing_location_spouse == 'Virtual'):
            # both parties (either together or separately) are signing virtually
            generated.append({'doc_type': 'RFO', 'form_number': 35})
            generated.append({'doc_type': 'RCP', 'form_number': 36})
            uploaded.append({'doc_type': 'OFI', 'party_code': 0})
            uploaded.append({'doc_type': 'EFSS', 'party_code': 1})
            if how_to_sign == 'Separately':
                uploaded.append({'doc_type': 'EFSS', 'party_code': 2})
            uploaded.append({'doc_type': 'RDP', 'party_code': 0})
            if has_children:
                uploaded.append({'doc_type': 'AAI', 'party_code': 0})
            if name_change_you:
                uploaded.append({'doc_type': 'NCV', 'party_code': 1})
            if name_change_spouse:
                uploaded.append({'doc_type': 'NCV', 'party_code': 2})
        else:
            return [], []

    else:  # Final Filing
        if signing_location_both == 'Virtual':
            # if both parties have signed virtually and signing together
            if has_children:
                uploaded.append({'doc_type': 'CSA', 'party_code': 0})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 0})

        elif signing_location_you == 'Virtual' and signing_location_spouse == 'Virtual':
            # both parties have signed virtually and signing separately
            if has_children:
                uploaded.append({'doc_type': 'CSA', 'party_code': 1})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 1})
            if has_children:
                uploaded.append({'doc_type': 'CSA', 'party_code': 2})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 2})

        elif (signing_location_both == 'In-person' or signing_location_you == 'In-person' or signing_location_spouse == 'In-person') and how_to_file == 'Online':
            # at least one party has signed with a commissioner and Filing Online
            generated.append({'doc_type': 'RFO', 'form_number': 35})
            generated.append({'doc_type': 'RCP', 'form_number': 36})
            if has_children:
                uploaded.append({'doc_type': 'CSA', 'party_code': 0})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 0})
            uploaded.append({'doc_type': 'OFI', 'party_code': 0})
            uploaded.append({'doc_type': 'EFSS', 'party_code': 1})
            uploaded.append({'doc_type': 'EFSS', 'party_code': 2})
            if has_children:
                uploaded.append({'doc_type': 'AAI', 'party_code': 0})
            if name_change_you:
                uploaded.append({'doc_type': 'NCV', 'party_code': 1})
            if name_change_spouse:
                uploaded.append({'doc_type': 'NCV', 'party_code': 2})
        else:
            return [], []

    return uploaded, generated


def get_filename(doc_type, party_code):
    form_name = Document.form_types[doc_type]
    slug = re.sub('[^0-9a-zA-Z]+', '-', form_name).strip('-')
    if party_code == 0:
        return slug + ".pdf"
    elif party_code == 1:
        return slug + "--Claimant1.pdf"
    else:
        return slug + "--Claimant2.pdf"
