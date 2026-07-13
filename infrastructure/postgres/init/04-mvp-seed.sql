-- RealtyAI MVP Seed Data

-- Organization
INSERT INTO organizations (id, name, plan)
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Edmonton Elite Realty', 'professional')
ON CONFLICT DO NOTHING;

-- User (Agent)
INSERT INTO users (id, organization_id, email, name, phone, role)
VALUES ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'sarah@eliterealty.com', 'Sarah Chen', '(555) 123-4567', 'agent')
ON CONFLICT DO NOTHING;

-- Agent Profile
INSERT INTO agent_profiles (id, user_id, brokerage, phone, license_number, preferences)
VALUES ('c3d4e5f6-a7b8-9012-cdef-123456789012', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
        'Edmonton Elite Realty', '(555) 123-4567', 'RE12345',
        '{"email_tone": "professional", "preferred_contact": "email", "marketing_style": "modern"}')
ON CONFLICT DO NOTHING;

-- Leads
INSERT INTO leads (id, agent_id, brokerage_id, first_name, last_name, email, phone, source, status, budget, location_interest, property_type_interest, timeline, pre_approved, ai_score, ai_score_reason, notes, last_contacted_at) VALUES
('d4e5f6a7-b8c9-0123-defa-234567890123', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 'John', 'Smith', 'john.smith@email.com', '(555) 123-4567', 'zillow', 'qualifying',
 550000, 'Windermere', 'single_family', '30_days', TRUE, 87,
 'Pre-approved. Active within 30 days. Responds quickly.',
 'Viewed 3 properties last week. Prefers newer builds.',
 NOW() - INTERVAL '1 day'),

('e5f6a7b8-c9d0-1234-efab-345678901234', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 'Sarah', 'Johnson', 'sarah.j@email.com', '(555) 987-6543', 'website', 'new',
 350000, 'Downtown', 'condo', '90_days', FALSE, 45,
 'Early stage. No pre-approval yet. Longer timeline.', NULL, NULL),

('f6a7b8c9-d0e1-2345-fabc-456789012345', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 'Mike', 'Chen', 'mike.chen@email.com', '(555) 555-1234', 'redfin', 'qualified',
 720000, 'Summerside', 'townhouse', 'immediate', TRUE, 92,
 'Pre-approved. Cash buyer. Ready to close.',
 'Very responsive. Looking for 3+ beds. Already sold his previous home.',
 NOW() - INTERVAL '6 hours'),

('a7b8c9d0-e1f2-3456-abcd-567890123456', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 'Emily', 'Davis', 'emily.d@email.com', '(555) 222-3333', 'referral', 'appointment_set',
 850000, 'Terwillegar', 'single_family', '60_days', TRUE, 78,
 'Referred by past client. Pre-approved. Has specific requirements.',
 'Wants walkout basement. Showing scheduled Saturday 2PM.',
 NOW() - INTERVAL '2 days'),

('b8c9d0e1-f2a3-4567-bcde-678901234567', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 'Robert', 'Wilson', 'rwilson@email.com', '(555) 444-5555', 'open_house', 'contacted',
 620000, 'Westside', 'single_family', '45_days', FALSE, 55,
 'Attended open house. Needs pre-approval. Moderate interest.',
 'Met at 123 Main open house. Has 2 kids, wants good school zone.',
 NOW() - INTERVAL '7 days');

-- Properties
INSERT INTO properties (id, agent_id, brokerage_id, address_street, address_city, address_state, address_zip, property_type, status, beds, baths, sqft, lot_size, year_built, garage_spaces, list_price, description, features, mls_number) VALUES
('c9d0e1f2-a3b4-5678-cdef-789012345678', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 '123 Main St', 'Edmonton', 'AB', 'T5J 1A4', 'single_family', 'active',
 4, 3, 2400, 6000, 2018, 2, 525000,
 'Beautifully renovated family home with modern kitchen, hardwood floors, and a private backyard oasis. Open concept main floor with natural light throughout.',
 '["Hardwood Floors", "Stainless Appliances", "Granite Countertops", "Central AC", "Fenced Yard", "Deck"]',
 'E1234567'),

('d0e1f2a3-b4c5-6789-defa-890123456789', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 '456 Oak Ave', 'Edmonton', 'AB', 'T5K 2B5', 'condo', 'active',
 2, 1, 1100, NULL, 2020, NULL, 275000,
 'Stunning downtown condo with panoramic skyline views. Floor-to-ceiling windows, modern finishes, and premium amenities including gym and rooftop patio.',
 '["In-suite Laundry", "Underground Parking", "Balcony", "Fitness Center", "Concierge"]',
 'E1234568'),

('e1f2a3b4-c5d6-7890-efab-901234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 '789 Pine Cres', 'Edmonton', 'AB', 'T6W 3C4', 'townhouse', 'active',
 3, 2.5, 1650, NULL, 2022, 1, 389900,
 'Modern townhouse in the family-friendly Summerside community. End unit with extra windows, upgraded kitchen, and low-maintenance yard.',
 '["Attached Garage", "Vaulted Ceilings", "Air Conditioning", "Walking Trails Nearby", "Lake Access"]',
 'E1234569'),

('f2a3b4c5-d6e7-8901-fabc-012345678901', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
 '321 Birch Blvd', 'Edmonton', 'AB', 'T6R 4D5', 'single_family', 'active',
 5, 4, 3200, 8500, 2015, 3, 789900,
 'Executive family home in prestigious Windermere. Gourmet kitchen, main-floor office, bonus room, and developed walkout basement with wet bar.',
 '["Gourmet Kitchen", "Walkout Basement", "3-Car Garage", "Central Vacuum", "Heated Floors", "Wet Bar"]',
 'E1234570');

-- Sample activity entries
INSERT INTO activities (id, organization_id, user_id, agent_name, action, intent, status, created_at) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
 'Lead Agent', 'Analyzed 5 leads for priority follow-up', 'lead', 'success', NOW() - INTERVAL '30 minutes'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567802', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
 'Marketing Agent', 'Generated listing campaign for 123 Main St', 'marketing', 'success', NOW() - INTERVAL '1 hour'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567803', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
 'Listing Agent', 'MLS description created for 321 Birch Blvd', 'listing', 'pending_approval', NOW() - INTERVAL '2 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567804', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
 'Document Agent', 'Reviewed purchase agreement - found 3 deadlines', 'document', 'success', NOW() - INTERVAL '3 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567805', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
 'Lead Agent', 'Automatic lead scoring completed', 'lead', 'success', NOW() - INTERVAL '4 hours');
