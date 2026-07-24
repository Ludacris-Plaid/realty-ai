import { Nav } from "@/components/splash/Nav";
import { Hero } from "@/components/splash/Hero";
import { ComplianceSection } from "@/components/splash/ComplianceSection";
import { Features } from "@/components/splash/Features";
import { DemoAccess } from "@/components/splash/DemoAccess";
import { Footer } from "@/components/splash/Footer";

export default function Home() {
  return (
    <>
      <Nav />
      <Hero />
      <ComplianceSection />
      <Features />
      <DemoAccess />
      <Footer />
    </>
  );
}