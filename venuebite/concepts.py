"""Small registry of canonical categories verified against Mapbox's category list."""

from dataclasses import dataclass
import re


def words(value):
    return tuple(re.findall(r"[\w]+", value.casefold()))


@dataclass(frozen=True)
class ConceptProfile:
    label: str
    category: str | None
    category_ids: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    @property
    def approximate(self):
        return self.category is None


# Aliases are input vocabulary, not additional provider category identifiers.
CONCEPTS = (
    ("Indian", "indian_restaurant", ("indian", "indian restaurant", "indian food"), ()),
    ("Mexican", "mexican_restaurant", ("mexican", "mexican restaurant", "mexican food"), ()),
    ("Cuban", "cuban_restaurant", ("cuban", "cuban restaurant", "cuban food"), ()),
    ("Pizza", "pizza_restaurant", ("pizza", "pizzeria", "pizza restaurant"), ()),
    ("Coffee", "coffee_shop", ("coffee", "coffee shop", "coffeehouse"), ("coffee", "coffee_roaster")),
    ("Burgers", "burger_restaurant", ("burger", "burgers", "burger restaurant"), ()),
    ("Cafe & bakery", "cafe", ("cafe", "cafe bakery", "cafe and bakery"), ("coffee_shop", "coffee", "bakery")),
    ("Bakery", "bakery", ("bakery", "bakeries"), ()),
    ("Restaurant", "restaurant", ("restaurant", "restaurants"), ()),
)
GENERIC_WORDS = {"restaurant", "restaurants", "food", "cuisine", "shop", "and", "the"}


def resolve_concept(value):
    normalized = " ".join(words(value))
    for label, category, aliases, related in CONCEPTS:
        if normalized in aliases:
            return ConceptProfile(label, category, (category, *related))
    keywords = tuple(word for word in words(value) if word not in GENERIC_WORDS)
    return ConceptProfile(value, None, keywords=keywords)


def classify_poi(poi, profile):
    categories = set(poi.category_ids) | set(poi.search_categories)
    if profile.category == "restaurant" or categories.intersection(profile.category_ids):
        return True, "Provider category"
    # Text results are not automatically direct matches: require literal concept words.
    keywords = profile.keywords if profile.approximate else words(profile.label)
    available = set(words(" ".join((poi.name, *poi.categories))))
    if keywords and all(keyword in available for keyword in keywords):
        return True, "Approximate text match"
    return False, "General restaurant"
