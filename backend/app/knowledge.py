HOTEL = {
 "name": "Aurelia Hotel", "check_in": "3:00 PM", "check_out": "11:00 AM", "reception": "24 hours",
 "breakfast": "Daily 7:00–10:30 AM in the Garden Room; included with Aurelia Suite stays.",
 "pool": "Heated indoor pool open 6:00 AM–10:00 PM.", "wifi": "Complimentary high-speed Wi-Fi throughout the hotel.",
 "parking": "On-site parking is available for $18 per night.", "accessibility": "Accessible rooms and step-free public access are available on request.",
 "luggage": "Complimentary luggage storage is available before check-in and after check-out.",
 "policies": "Check-in requires a photo ID. No smoking indoors. Demo information only; no real booking is made."
}
ROOMS = [
 {"id":"standard-room","name":"Standard Room","description":"A comfortable, efficient room for short city stays.","capacity":2,"beds":"1 queen bed","amenities":["Wi-Fi","work desk","walk-in shower"],"price_per_night":129,"inventory":8,"suitable_for":["solo travelers","couples"]},
 {"id":"deluxe-room","name":"Deluxe Room","description":"A brighter room with more space and a city view.","capacity":2,"beds":"1 king bed","amenities":["Wi-Fi","city view","armchair","walk-in shower"],"price_per_night":179,"inventory":5,"suitable_for":["couples","business travelers"]},
 {"id":"premium-room","name":"Premium Room","description":"A quiet, spacious room with upgraded amenities and a garden outlook.","capacity":2,"beds":"1 king bed","amenities":["Wi-Fi","garden view","Nespresso machine","soaking tub"],"price_per_night":239,"inventory":3,"suitable_for":["couples","quiet stays"]},
 {"id":"family-room","name":"Family Room","description":"A flexible room designed for families and small groups.","capacity":4,"beds":"1 king bed and 2 twin beds","amenities":["Wi-Fi","sofa bed","mini fridge","two bathrooms"],"price_per_night":269,"inventory":4,"suitable_for":["families","small groups"]},
 {"id":"aurelia-suite","name":"Aurelia Suite","description":"Our most spacious suite with a separate sitting area.","capacity":3,"beds":"1 king bed and sofa bed","amenities":["Wi-Fi","separate lounge","bathtub","complimentary breakfast"],"price_per_night":389,"inventory":2,"suitable_for":["special occasions","longer stays"]}
]

def room_by_id(room_id): return next((r for r in ROOMS if r["id"] == room_id), None)
def search_rooms(guests=1): return [r for r in ROOMS if r["capacity"] >= guests]
