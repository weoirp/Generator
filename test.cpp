#include <string>
#include <vector>

namespace XXX {

struct NoConstructor {
	static NoConstructor *new_instance() { }

	std::string getString() {	}

	int setInterger(int &interger) {	}

	~NoConstructor() { }
};

enum Kind {
	Dog,
	Cat,
};

enum class PetKind {
	Dog = 10,
	Cat,
	Fish,
	Bird,
	Rabbit,
	Hamster,
	Other
};

class Pet {
public:
	Pet(const std::string &name, const PetKind &species) 
		: m_name(name), m_species(species) {}
	/// 注释注释
	std::string name() const { return m_name; }
	PetKind species() const { return m_species; }

	class Active {
	public:
		Active(Pet &pet) : m_pet(pet) {}
		void run() const { m_pet.run(); }
	private:
		Pet &m_pet;
	};

	virtual void run() const;
private:
	const std::string m_name;
	PetKind m_species;
};

namespace Dog {
class Dog : private Pet{
public:
	Dog(const std::string &name) : Pet(name, PetKind::Dog) {}
	std::string bark() const { return "Woof!"; }
};
}

class Rabbit : protected Pet {
public:
	Rabbit(const std::string &name) : Pet(name, PetKind::Rabbit) {}
	void run() const override;
};

class Hamster : protected Pet {
public:
	Hamster(const std::string &name) : Pet(name, PetKind::Hamster) {} 
	void run() const final;
};

class Chimera: public Rabbit, public Hamster {
public:
	Chimera() : Rabbit("Kimmy"), Hamster("Joey"), kind(PetKind::Other) {}
	const static int Id = 1;
private:;
	static int Num;
	const PetKind kind;
};

static int a = 1;
const static std::string world="world";
std::string b;

static Dog::Dog function1(const Rabbit &r, Hamster *h=NULL, Chimera c)
{

}

const int function2(int param1=123, char *param2=nullptr, double &param3);

}

extern void function3();

auto la = [](int x, int y) -> int { return x + y; };

class ABC {};