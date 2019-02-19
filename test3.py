import random
import time


# Variables of RandomWordGenerator

length_of_word = 5
c = 0
no_of_words = 0

st=""
def generate_random_character():
    options=random.randint(0,1)

    if options == 0:
        c = random.randint(65,90)
    else:
        c = random.randint(97,122)

    return c

def generate_random_word():
    st=""
    for i in range(0,random.randint(2,10)):
        st=st+chr(generate_random_character())

    return st


def generate_random_words(filename, n):

    file = open(filename, 'w')

    no_of_random_words = n

    for i in range(0,no_of_random_words):

        if i % 15 == 0:
            file.write('\n')
        file.write(generate_random_word())
        file.write(' ')

    file.close()

start=time.time()
generate_random_words('abc.txt', 10000000)
print("Total time: %s seconds" %(time.time()-start))