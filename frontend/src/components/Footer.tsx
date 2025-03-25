const Footer = () => {
  return (
    <footer className="w-full bg-white border-t border-gray-200 py-4 mt-auto">
      <div className="container mx-auto px-4">
        <div className="flex justify-center items-center">
          <p className="text-sm text-gray-600">
            © {new Date().getFullYear()} Prae8. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
