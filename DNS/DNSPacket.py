import bitstring


class DNSPacket:

    def __init__(self, header=None, question=None, answer=None, authority=None, additional=None):
        self.header = header
        self.question = question
        self.answer = answer
        self.authority = authority
        self.additional = additional

    def to_bytes(self):
        result = self.header.to_bytes()
        if self.question is not None:
            for index in range(len(self.question)):
                result += self.question[index].to_bytes()
        if self.answer is not None:
            for index in range(len(self.answer)):
                result += self.answer[index].to_bytes()
        if self.authority is not None:
            for index in range(len(self.authority)):
                result += self.authority[index].to_bytes()
        if self.additional is not None:
            for index in range(len(self.additional)):
                result += self.additional[index].to_bytes()
        return result


class Header:

    def __init__(self, id, qr=0, opcode=0, authoritative=0, truncated=0, recursion_desired=0,
                 recursion_available=0, reply_code=0, questions=0, answer_rrs=0, authority_rrs=0, additional_rrs=0):
        self.id = id  # Идентификация
        self.qr = qr  # Тип сообщения: 0 - запрос, 1 - ответ
        self.opcode = opcode  # Код операции: 0 - стандарт, 1 - инверсный, 2 - статус сервера
        self.aa = authoritative  # Авторитетный ответ
        self.tc = truncated  # Обрезано
        self.rd = recursion_desired  # Требуется рукурсия
        self.ra = recursion_available  # Рекурсия возможна
        self.rcode = reply_code  # Код возврата: 3 - имени домена не существует
        self.qdcount = questions  # Количество вопросов
        self.ancount = answer_rrs  # Количество обычных ответов
        self.nscount = authority_rrs  # Полномочный источник
        self.arcount = additional_rrs  # Дополнительная информация

    def to_bytes(self):
        bits_packet = bitstring.BitArray(length=96)
        bits_packet[0:16] = bitstring.pack('uint: 16', self.id)
        bits_packet[16:17] = bitstring.pack('uint: 1', self.qr)
        bits_packet[17:21] = bitstring.pack('uint: 4', self.opcode)
        bits_packet[21:22] = bitstring.pack('uint: 1', self.aa)
        bits_packet[22:23] = bitstring.pack('uint: 1', self.tc)
        bits_packet[23:24] = bitstring.pack('uint: 1', self.rd)
        bits_packet[24:25] = bitstring.pack('uint: 1', self.ra)
        bits_packet[28:32] = bitstring.pack('uint: 4', self.rcode)
        bits_packet[32:48] = bitstring.pack('uint: 16', self.qdcount)
        bits_packet[48:64] = bitstring.pack('uint: 16', self.ancount)
        bits_packet[64:80] = bitstring.pack('uint: 16', self.nscount)
        bits_packet[80:96] = bitstring.pack('uint: 16', self.arcount)
        return bits_packet.tobytes()

    def set_id(self, id):
        self.id = id

    def set_ancount(self, n):
        self.ancount = n


class Question:
    def __init__(self, qname, qtype, qclass):
        self.qname = qname  # Доменное имя
        self.qtype = qtype  # Тип запроса: 1-А, 2-NS, 5-СNAME, 6-SOA, 12-PTR, 28-AAAA
        self.qclass = qclass  # Класс запроса

    def to_bytes(self):
        bytes_name = name_to_bytes(self.qname)[0]
        bits_packet = bitstring.BitArray(length=32)
        bits_packet[0:16] = bitstring.pack('uint: 16', self.qtype)
        bits_packet[16:32] = bitstring.pack('uint: 16', self.qclass)
        return bytes_name + bits_packet.tobytes()


class Answer:
    def __init__(self, aname, atype, aclass, ttl, data_length, address):
        self.aname = aname  # Доменное имя
        self.atype = atype  # Тип запроса
        self.aclass = aclass  # Класс запроса
        self.ttl = ttl  # Время жизни записи в кеше
        self.rdlength = data_length  # Размер данных
        self.rdata = address  # адресс

    def __str__(self):
        return f'    Name: {self.aname}\n' \
               f'    Type: ({self.atype})\n' \
               f'    Class: IN ({self.aclass})\n' \
               f'    Time to live: {self.ttl}\n' \
               f'    Data length: {self.rdlength}\n' \
               f'    Address: {self.rdata}\n'

    def __eq__(self, other):
        return self.aname == other.aname and self.atype == other.atype \
               and self.aclass == other.aclass and self.ttl == other.ttl \
               and self.rdlength == other.rdlength and self.rdata == other.rdata

    def to_bytes(self):
        bytes_name = name_to_bytes(self.aname)[0]
        bits_packet = bitstring.BitArray()
        bits_packet[0:16] = bitstring.pack('uint: 16', self.atype)
        bits_packet[16:32] = bitstring.pack('uint: 16', self.aclass)
        bits_packet[32:64] = bitstring.pack('uint: 32', self.ttl)
        if self.atype == 1:
            address = address_to_bytes(self.rdata)
            bits_packet[64:86] = bitstring.pack('uint: 16', self.rdlength)
        else:
            address, length = name_to_bytes(self.rdata)
            bits_packet[64:86] = bitstring.pack('uint: 16', length)
        return bytes_name + bits_packet.tobytes() + address


def get_bit_packet(data):
    return bitstring.Bits(data)


def read_header(bit_packet: bitstring.Bits):
    id = bit_packet[0:16].uint
    qr = bit_packet[16:17].uint
    opcode = bit_packet[17:21].uint
    aa = bit_packet[21:22].uint
    tc = bit_packet[22:23].uint
    rd = bit_packet[23:24].uint
    ra = bit_packet[24:25].uint
    rcode = bit_packet[28:32].uint
    qcount = bit_packet[32:48].uint
    ancount = bit_packet[48:64].uint
    nscount = bit_packet[64:80].uint
    arcount = bit_packet[80:96].uint
    return Header(id, qr, opcode, aa, tc, rd, ra,
                  rcode, qcount, ancount, nscount, arcount)


def read_questions(bit_packet: bitstring.Bits, header: Header):
    questions = []
    start_index = 96
    for index in range(header.qdcount):
        question, end_index = read_question(bit_packet, start_index)
        questions.append(question)
        start_index = end_index
    return questions, start_index


def read_question(bit_packet: bitstring.Bits, start_index):
    qname, end_name_index = read_name(bit_packet, start_index, name='')
    qtype = bit_packet[end_name_index:end_name_index + 16].uint
    qclass = bit_packet[end_name_index + 16:end_name_index + 32].uint
    return Question(qname, qtype, qclass), end_name_index + 32


def read_answers(bit_packet: bitstring.Bits, header: Header, start_index):

    def get_answers(count, start_index):
        if count > 0:
            answers = []
            for index in range(count):
                answer, end_index = read_answer(bit_packet, start_index)
                answers.append(answer)
                start_index = end_index
            return answers, start_index
        else:
            return [], start_index

    answers_rrs, start_index = get_answers(header.ancount, start_index)
    authority_rrs, start_index = get_answers(header.nscount, start_index)
    additional_rrs, start_index = get_answers(header.arcount, start_index)

    return answers_rrs, authority_rrs, additional_rrs


def read_answer(bit_packet: bitstring.Bits, start_index):
    aname, end_name_index = read_name(bit_packet, start_index, name='')
    atype = bit_packet[end_name_index:end_name_index + 16].uint
    aclass = bit_packet[end_name_index + 16:end_name_index + 32].uint
    ttl = bit_packet[end_name_index + 32:end_name_index + 64].uint
    data_length = bit_packet[end_name_index + 64: end_name_index + 80].uint
    address, end_index = read_address(bit_packet, end_name_index + 80, data_length, atype)
    return Answer(aname, atype, aclass, ttl, data_length, address), end_index


def read_name(bit_packet: bitstring.Bits, index, name):
    count_of_char = bit_packet[index:index + 8].uint
    while count_of_char != 0:
        if count_of_char >= 192:
            hoop_place = bit_packet[index + 2:index + 16].uint * 8
            name = read_name(bit_packet, hoop_place, name)[0]
            return name, index + 16
        else:
            index += 8
            for i in range(count_of_char):
                name += bit_packet[index:index + 8].bytes.decode('ASCII')
                index += 8
            name += '.'
        count_of_char = bit_packet[index:index + 8].uint
    else:
        return name[:-1], index + 8


def read_address(bit_packet: bitstring.Bits, index, data_length, address_type):
    if address_type == 1:
        address = ''
        for i in range(data_length):
            address += str(bit_packet[index:index + 8].uint)
            index = index + 8
            address += '.'
        return address[:-1], index
    elif address_type == 2:
        address, index = read_name(bit_packet, index, name='')
        return address, index


def name_to_bytes(name):
    bits_name = bitstring.BitArray()
    name_parts_array = name.split('.')
    name_length = 0
    index = 0
    for name_part in name_parts_array:
        bits_name[index:index + 8] = bitstring.pack('uint: 8', len(name_part))
        name_length += len(name_part) + 1
        index += 8
        for char in name_part:
            bits_name[index:index + 8] = bitstring.pack('hex: 8', char.encode('ASCII').hex())
            index += 8
    bits_name[index: index + 8] = bitstring.pack('uint: 8', 0)
    name_length += 1
    return bits_name.tobytes(), name_length


def address_to_bytes(address):
    bits_address = bitstring.BitArray()
    address_parts_array = address.split('.')
    index = 0
    for address_part in address_parts_array:
        address = int(address_part)
        bits_address[index:index + 8] = bitstring.pack('uint: 8', address)
        index += 8
    return bits_address.tobytes()


def read_dns_packet(data):
    bit_data = get_bit_packet(data)
    header = read_header(bit_data)
    questions, index = read_questions(bit_data, header)
    answer_rrs, authority_rrs, additional_rrs = read_answers(bit_data, header, index)
    return DNSPacket(header, questions, answer_rrs, authority_rrs, additional_rrs)