class ContactData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    # in reference to
    # http://en.wikipedia.org/wiki/VCard
    TEL = StringCol()
    UID = StringCol()
    PHOTO = BLOBCol()
    N = StringCol()
    FN = StringCol()
    # contains all data as serialized vc, including the above columns
    data = BLOBCol()



    # TODO: support other formats + limit the list
    def contact_list(self, limit = 200, format = 'json', q = False, timestamp = 0):
        if q:
            import base64
            contacts = ContactData.select()
            return "\n".join(["%s <%s>" % (contact.FN, contact.TEL) for contact in contacts])
        else:
            import base64
            contacts = ContactData.select()
            return json.dumps([{
                'TEL':    contact.TEL,
                'N':      contact.N,
                'UID':    contact.UID,
                'PHOTO':    base64.b64encode(contact.PHOTO),
                'FN':     contact.FN,} for contact in contacts])
    contact_list.exposed = True


    def import_vcard(self, vcard_file = ''):
        """ given a vcard_file FieldStorage object, import vCards """
        try:
            vs = vobject.readComponents(vcard_file.value)
            for v in vs:
                # TODO: filter out contacts that don't have a telephone number
                ContactData(FN=v.fn.value,
                    TEL=v.tel.value,
                    PHOTO=v.photo.value,
                    UID='blah', #TODO: implement UID checking / generation
                    N="%s %s" % (v.n.value.given, v.n.value.family),
                    data=str(v.serialize()))
            return 'Contact saved'
        except Exception, e:
            print e
            return "This contact could not be saved"
    import_vcard.exposed = True

    def export_vcard(self):
        contacts = ContactData.select()
        contact_string = "\n".join([contact.data for contact in contacts])
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=vCards.vcf"
        return contact_string
    export_vcard.exposed = True



