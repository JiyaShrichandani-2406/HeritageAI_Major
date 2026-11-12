import { Link } from "react-router-dom";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Button from "../components/ui/button.jsx";

export default function NotFound() {
  return (
    <>
      <NavBar />
      <main className="container-page py-24 text-center">
        <div className="eyebrow">404</div>
        <h1 className="font-heading text-4xl md:text-5xl font-bold mt-2">We couldn't find that page</h1>
        <p className="mt-3 text-ink-500">The link may be outdated. Head back to the home page to continue exploring.</p>
        <div className="mt-6">
          <Button as={Link} to="/">Return home</Button>
        </div>
      </main>
      <Footer />
    </>
  );
}
